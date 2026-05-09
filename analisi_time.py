import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots 


GUIDA_TIMELINE = """ Vedi se il settore target è in crescita, in declino o se ha un andamento periodico legato a bandi stagionali"""
GUIDA_TIMEMAP = """I mesi più intensi indicano quando le aziende ricevono più liquidità. Individua i momenti migliori per proporre nuovi investimenti"""
GUIDA_CAGR = r"""
#### 📈 Guida al CAGR (Compound Annual Growth Rate)

Il **CAGR** misura la crescita media annua del **Settore Target**, ipotizzando una progressione costante.

$$CAGR = \left( \frac{\text{Valore Finale}}{\text{Valore Iniziale}} \right)^{\frac{1}{n}} - 1$$

1.  **Anno Zero**: Tutti i calcoli partono dal primo anno del dataset (es. 2020).
2.  **Primo Anno**: Nel primo anno dopo l'inizio ($n=1$), il CAGR coincide con la *crescita semplice*. 
3.  **Anni Successivi**: I valori si "ammorbidiscono" perché la crescita totale viene spalmata (composta) su più anni rispetto all'anno zero.

**Esempio:** Un CAGR del 10% su 3 anni significa che, partendo dal valore iniziale, il settore è cresciuto mediamente del 10% ogni anno per tre anni di fila.

💡 Usa il CAGR per capire se il **Settore Target** è un settore in crescita su cui ha senso investire!
"""



def time_analysis(df):
    """
    Renderizza l'analisi temporale con grafici a linee perfettamente sincronizzati
    e collegati da una Spike Line verticale unica (hover unificato).
    """
    # --- 1. Preparazione Dati Locale (Invariata) ---
    df_temp = df.copy()
    df_temp['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_temp['RNA_DATA_CONCESSIONE'])
    df_temp['AnnoMonth'] = df_temp['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
    df_temp['Anno'] = df_temp['RNA_DATA_CONCESSIONE'].dt.year
    df_temp['Mese_Num'] = df_temp['RNA_DATA_CONCESSIONE'].dt.month
    
    # Aggregazione
    df_time_tot = df_temp.groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_time_targ = df_temp[df_temp['IS_TARGET'] == 1].groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    
    df_time_plot = pd.merge(df_time_tot, df_time_targ, on='AnnoMonth', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
    df_time_plot.columns = ['Periodo', 'Mercato Totale', 'Settore Target']
    
    # Calcoli per i grafici
    df_time_plot['Quota Target (%)'] = (df_time_plot['Settore Target'] / df_time_plot['Mercato Totale'] * 100).fillna(0)
    df_time_plot['Mercato_Mln'] = df_time_plot['Mercato Totale'] / 1e6
    df_time_plot['Target_Mln'] = df_time_plot['Settore Target'] / 1e6

    # Range per sincronizzare perfettamente l'asse X (Invariato)
    x_min = df_time_plot['Periodo'].min()
    x_max = df_time_plot['Periodo'].max()

    # --- INIZIO COSTRUZIONE FIGURA UNICA ---
    st.write("")
    with st.popover("💡 Strategia"):
        st.info(GUIDA_TIMELINE)
    
    # 2. Creazione della Figura con Subplots (2 righe, 1 colonna)
    # shared_xaxes=True è la chiave per la sincronizzazione del puntatore
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08, # Spazio tra i due grafici
        subplot_titles=("Quota di Mercato del Settore Target", "Evoluzione Temporale del Budget (Mln €)")
    )

    # --- A. AGGIUNTA TRACCE AL GRAFICO SUPERIORE (Row 1) ---
    # Quota Target (%) - Area chart
    fig.add_trace(
        go.Scatter(
            x=df_time_plot['Periodo'], 
            y=df_time_plot['Quota Target (%)'],
            name="Quota Target (%)",
            line=dict(color='#e74c3c', width=2, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.2)', # Rosso trasparente
            mode='lines+markers',
            marker=dict(size=6)
        ),
        row=1, col=1
    )

    # --- B. AGGIUNTA TRACCE AL GRAFICO INFERIORE (Row 2) ---
    # Mercato Totale (Mln €) - Linea Blu
    fig.add_trace(
        go.Scatter(
            x=df_time_plot['Periodo'], 
            y=np.sqrt(df_time_plot['Mercato_Mln']),
            name="Mercato Totale",
            line=dict(color='#3498db', width=2, shape='spline'),
            mode='lines+markers',
            marker=dict(size=6),
            # Tooltip custom per mostrare il valore reale (non la radice)
            hovertemplate="Mercato Totale: %{text:.2f} Mln €<extra></extra>",
            text=df_time_plot['Mercato_Mln']
        ),
        row=2, col=1
    )
    
    # Settore Target (Mln €) - Linea Rossa
    fig.add_trace(
        go.Scatter(
            x=df_time_plot['Periodo'], 
            y=np.sqrt(df_time_plot['Target_Mln']),
            name="Settore Target",
            line=dict(color='#e74c3c', width=2, shape='spline'),
            mode='lines+markers',
            marker=dict(size=6),
            hovertemplate="Settore Target: %{text:.2f} Mln €<extra></extra>",
            text=df_time_plot['Target_Mln']
        ),
        row=2, col=1
    )

    # --- C. CONFIGURAZIONE LAYOUT E ASSI (La parte complessa) ---
    # Calcolo Tick asse Y inferiore (Scala Radice Quadrata)
    max_mln = df_time_plot['Mercato_Mln'].max()
    potential_ticks = np.array([0, 1, 5, 10, 25, 50, 100, 200, 400, 800])
    tick_vals = potential_ticks[potential_ticks <= max_mln]
    if max_mln not in tick_vals: tick_vals = np.append(tick_vals, max_mln)

    fig.update_layout(
        template="plotly_white",
        height=700, # Altezza totale aumentata per contenere entrambi
        margin=dict(l=80, r=40, t=50, b=50), # Margini fissi per allineamento
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        
        # --- HOVER UNIFICATO: La soluzione al tuo problema ---
        # Traccia una linea verticale attraverso TUTTA la figura (entrambi i grafici)
        hovermode="x unified",
        
        # Configurazione estetica della linea verticale (Spike)
        xaxis=dict(
            showspikes=True,
            spikemode='across+marker',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#999999'
        )
    )

    # Configurazione specifica Assi Y (yaxis per row 1, yaxis2 per row 2)
    fig.update_yaxes(
        title_text="Quota Target (%)", 
        ticksuffix="%", 
        gridcolor="#f0f0f0", 
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Budget (Mln €)", 
        tickmode='array',
        tickvals=np.sqrt(tick_vals),
        ticktext=[f"{v:.1f}" for v in tick_vals],
        gridcolor="#f0f0f0",
        row=2, col=1
    )

    # Configurazione specifica Assi X (xaxis per row 1, xaxis2 per row 2)
    #shared_xaxes=True nasconde automaticamente l'asse X del primo grafico
    fig.update_xaxes(
        range=[x_min, x_max], 
        constrain='domain', 
        gridcolor="#e1e1e1", 
        griddash="dot", 
        row=1, col=1
    )
    
    fig.update_xaxes(
        title_text="Periodo", 
        range=[x_min, x_max], 
        constrain='domain', 
        gridcolor="#e1e1e1", 
        griddash="dot", 
        row=2, col=1
    )

    # Rendering
    st.plotly_chart(fig, use_container_width=True, key="temporal_subplots")
    
    

  
    # --- HEATMAP (STAGIONALITÀ) ---
    st.divider()
    st.write("")
    st.subheader("🔥 Intensità delle Concessioni per Mese e Anno")
    st.write("")
    with st.popover("💡 Strategia"):
        st.info(GUIDA_TIMEMAP)
    st.write("")
              
    df_heat_data = df_temp[df_temp['IS_TARGET'] == 1].groupby(['Anno', 'Mese_Num'])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    pivot_heat = df_heat_data.pivot(index='Anno', columns='Mese_Num', values='RNA_ELEMENTO_DI_AIUTO').fillna(0)
    pivot_heat = pivot_heat.sort_index(ascending=False)
    
    mesi_ita = {1:'Gen', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mag', 6:'Giu', 7:'Lug', 8:'Ago', 9:'Set', 10:'Ott', 11:'Nov', 12:'Dic'}
    pivot_heat.columns = [mesi_ita.get(c, c) for c in pivot_heat.columns]
    
    fig_heat = px.imshow(
        pivot_heat,
        labels=dict(x="Mese", y="Anno", color="Budget (€)"),
        x=pivot_heat.columns,
        y=[str(a) for a in pivot_heat.index],
        color_continuous_scale="Reds",
        text_auto=".2s"
    )
    
    fig_heat.update_layout(
        coloraxis_colorbar_title_text="",
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(type='category', autorange="reversed")
    )
    
    st.plotly_chart(fig_heat, use_container_width=True, key="heatmap_stagionalita")

    # --- TABELLA DI ANALISI STAGIONALE E MARKETING ---
    st.write("")
    st.subheader("📊 Classifica Stagionale del Budget Target")
    
    # 1. Calcolo la somma del budget per ogni mese su tutta la serie storica
    df_mesi_stat = df_temp[df_temp['IS_TARGET'] == 1].groupby('Mese_Num')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    
    # Calcolo il totale complessivo per la normalizzazione
    tot_budget_target = df_mesi_stat['RNA_ELEMENTO_DI_AIUTO'].sum()
    
    if tot_budget_target > 0:
        # 2. Normalizzazione: Calcolo il peso percentuale
        df_mesi_stat['Peso %'] = (df_mesi_stat['RNA_ELEMENTO_DI_AIUTO'] / tot_budget_target * 100)
        
        # 3. Preparazione per la visualizzazione
        # Aggiungiamo i nomi dei mesi
        df_mesi_stat['Mese'] = df_mesi_stat['Mese_Num'].map(mesi_ita)
        
        # Ordiniamo dal migliore al peggiore
        df_rank = df_mesi_stat.sort_values('Peso %', ascending=False).reset_index(drop=True)
        
        # Rinominiamo le colonne per l'utente finale
        df_rank = df_rank[['Mese', 'RNA_ELEMENTO_DI_AIUTO', 'Peso %']]
        df_rank.columns = ['Mese', 'Budget Totale (€)', 'Incidenza %']
        
        # 4. Visualizzazione Tabellare con Formattazione
        col1, col2, col3 = st.columns([1, 2, 2]) 
        with col1:
            st.dataframe(
                df_rank.style.format({
                    'Budget Totale (€)': '{:,.0f} €',
                    'Incidenza %': '{:.2f} %'
                }).bar(subset=['Incidenza %'], color='#ff4b4b', vmin=0, vmax=df_rank['Incidenza %'].max()),
                use_container_width=True,
                hide_index=True
            )
        
        # --- 5. INSIGHT AUTOMATICO SUI PERIODI SPOT ---
        top_mese = df_rank.iloc[0]['Mese']
        peso_top = df_rank.iloc[0]['Incidenza %']
        
        st.info(f"""
        🎯 **Insight Operativo:** Il mese di **{top_mese}** è il periodo spot più rilevante, 
        concentrando da solo il **{peso_top:.1f}%** delle risorse totali allocate storicamente. 
        Si consiglia di pianificare le campagne di acquisizione clienti con un anticipo di 30-45 giorni rispetto ai primi 3 mesi in classifica.
        """)
        
    else:
        st.warning("Nessun dato disponibile per generare la classifica stagionale.")



    
    # --- ANALISI STORICA ---
    st.divider()
    st.write("")
    st.subheader("📈 Analisi Storica: Aiuto Medio vs Crescita Composta")
    st.write("")
    with st.popover("💡 Guida alla lettura e Strategia"):
        st.info(GUIDA_CAGR)
    st.write("")
    
    import datetime
    anno_corrente = datetime.datetime.now().year

    # 1. Raggruppamento e Calcoli core
    df_annual = df_temp.groupby('Anno').agg(
        Aiuti_Tot=('RNA_ELEMENTO_DI_AIUTO', 'count'),
        Aiuti_Target=('IS_TARGET', 'sum'),
        Vol_Tot=('RNA_ELEMENTO_DI_AIUTO', 'sum'),
        Vol_Target=('RNA_ELEMENTO_DI_AIUTO', lambda x: df_temp.loc[x.index, 'RNA_ELEMENTO_DI_AIUTO'][df_temp['IS_TARGET'] == 1].sum())
    ).reset_index().sort_values('Anno')

    def calc_cagr(current_val, start_val, current_year, start_year):
        n_anni = current_year - start_year
        if n_anni <= 0 or start_val <= 0 or current_val <= 0: return 0.0
        return (current_val / start_val) ** (1 / n_anni) - 1

    anno_start = df_annual['Anno'].min()
    prat_target_start = df_annual['Aiuti_Target'].iloc[0] 
    vol_target_start = df_annual['Vol_Target'].iloc[0]

    # Calcolo metriche strategiche
    df_annual['Aiuto_Medio_Target'] = (df_annual['Vol_Target'] / df_annual['Aiuti_Target']).fillna(0)
    df_annual['Quota Target (%)'] = (df_annual['Aiuti_Target'] / df_annual['Aiuti_Tot'] * 100).fillna(0)
    df_annual['Quota Vol. Target (%)'] = (df_annual['Vol_Target'] / df_annual['Vol_Tot'] * 100).fillna(0)
    df_annual['CAGR Target'] = df_annual.apply(lambda x: calc_cagr(x['Aiuti_Target'], prat_target_start, x['Anno'], anno_start) * 100, axis=1)
    df_annual['CAGR Vol. Target'] = df_annual.apply(lambda x: calc_cagr(x['Vol_Target'], vol_target_start, x['Anno'], anno_start) * 100, axis=1)

    # Mascheramento anno in corso per i CAGR
    df_annual.loc[df_annual['Anno'] == anno_corrente, ['CAGR Target', 'CAGR Vol. Target']] = None

    # --- PARTE SUPERIORE: IL GRAFICO ---
    fig_strategy = make_subplots(specs=[[{"secondary_y": True}]])

    # Barre: Ticket Medio
    fig_strategy.add_trace(
        go.Bar(
            x=df_annual['Anno'],
            y=df_annual['Aiuto_Medio_Target'],
            name="Ticket Medio (€)",
            marker_color='rgba(52, 152, 219, 0.6)',
            hovertemplate="Anno %{x}<br>Aiuto Medio: € %{y:,.0f}<extra></extra>"
        ), secondary_y=False
    )

    # Linea: CAGR Volume (solo anni completi)
    df_cagr_plot = df_annual.dropna(subset=['CAGR Vol. Target'])
    fig_strategy.add_trace(
        go.Scatter(
            x=df_cagr_plot['Anno'],
            y=df_cagr_plot['CAGR Vol. Target'],
            name="CAGR Vol. Target (%)",
            line=dict(color='#2ecc71', width=4, shape='spline'),
            mode='lines+markers+text',
            text=[f"{v:.1f}%" if v != 0 else "" for v in df_cagr_plot['CAGR Vol. Target']],
            textposition="top center",
            hovertemplate="Anno %{x}<br>CAGR: %{y:.2f}%<extra></extra>"
        ), secondary_y=True
    )

    fig_strategy.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
        template="plotly_white",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    fig_strategy.update_yaxes(title_text="Aiuto Medio (€)", secondary_y=False, tickformat="€,.0f")
    fig_strategy.update_yaxes(title_text="CAGR (%)", secondary_y=True, ticksuffix="%")
    fig_strategy.update_xaxes(type='category')

    st.plotly_chart(fig_strategy, use_container_width=True)

    # --- PARTE INFERIORE: LA TABELLA DETTAGLIATA ---
    

    # Formattazione per la visualizzazione tabella
    df_view = df_annual.sort_values('Anno', ascending=False).copy()
    df_view['Vol. Tot. (€)'] = df_view['Vol_Tot'].apply(lambda x: f"€ {x/1e6:.2f}M")
    df_view['Vol. Target (€)'] = df_view['Vol_Target'].apply(lambda x: f"€ {x/1e6:.2f}M")

    df_final = df_view[[
        'Anno', 'Aiuti_Tot', 'Aiuti_Target', 'Quota Target (%)', 'CAGR Target',
        'Vol. Tot. (€)', 'Vol. Target (€)', 'Quota Vol. Target (%)', 'CAGR Vol. Target'
    ]]

    df_final.columns = [
        'Anno', 'Aiuti Tot.', 'Aiuti Target', 'Quota Target (%)', 'CAGR Target',
        'Vol. Tot. (€)', 'Vol. Target (€)', 'Quota Vol. Target (%)', 'CAGR Vol. Target'
    ]

    def color_cagr(val):
        try:
            if val is None or pd.isna(val): return ''
            v = float(val)
            if v > 0.001: return 'color: #27ae60; font-weight: bold;'
            if v < -0.001: return 'color: #e74c3c; font-weight: bold;'
        except: pass
        return ''

    st_df = df_final.style.map(
        color_cagr, subset=['CAGR Target', 'CAGR Vol. Target']
    ).format({
        'CAGR Target': "{:.2f} %", 'CAGR Vol. Target': "{:.2f} %",
        'Quota Target (%)': "{:.2f} %", 'Quota Vol. Target (%)': "{:.2f} %"
    }, na_rep="In corso...")

    st.write("")
    st.write("")
    st.dataframe(st_df, hide_index=True, use_container_width=True)

    
# --- INTERPRETAZIONE FINALE INTEGRALE (16 SCENARI PIATTI) ---
    if len(df_annual) >= 2:
        df_valid = df_annual.dropna(subset=['CAGR Vol. Target'])
        ultimo = df_valid.iloc[-1]
        penultimo = df_valid.iloc[-2]
        
        # Variabili Decisionali
        cagr_att = ultimo['CAGR Vol. Target']
        c_pre = penultimo['CAGR Vol. Target']
        diff_cagr = cagr_att - c_pre
        diff_aiuto = ultimo['Aiuto_Medio_Target'] - penultimo['Aiuto_Medio_Target']
        diff_n = int(ultimo['Aiuti_Target'] - penultimo['Aiuti_Target'])
        
        # Dati pronti per le f-string
        anno_u = int(ultimo['Anno'])
        anno_p = int(penultimo['Anno'])
        a_med = ultimo['Aiuto_Medio_Target']
        
        # Calcolo quote percentuali
        p_aiuto = (diff_aiuto / penultimo['Aiuto_Medio_Target'] * 100) if penultimo['Aiuto_Medio_Target'] > 0 else 0
        p_n = (diff_n / penultimo['Aiuti_Target'] * 100) if penultimo['Aiuti_Target'] > 0 else 0

        st.write("")

        # --- AREA 1: CAGR POSITIVO + ACCELERAZIONE ---

        if cagr_att > 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n > 0:
            st.success("🚀 **BOOM TOTALE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante l'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target è in piena espansione: aumentano contemporaneamente il numero di progetti e il loro valore economico.
            """)

        elif cagr_att > 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n <= 0:
            st.success("🚀 **ACCELERAZIONE E VALORE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Grazie al calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target è in accelerazione e sta puntando su meno aiuti prioritari dal peso maggiore.
            """)

        elif cagr_att > 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n > 0:
            st.success("🚀 **ACCELERAZIONE E DIFFUSIONE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è diminuito di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target è in accelerazione e sta puntando sulla capillarità: fornendo più aiuti ma dal peso minore.
            """)

        elif cagr_att > 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.warning("⚠️ **ANOMALIA STATISTICA (INERZIA STORICA)**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il trend storico accelera per inerzia, ma l'anno corrente segna una contrazione reale su tutti i fronti. Verificare la saturazione del mercato.
            """)

        # --- AREA 2: CAGR POSITIVO + RALLENTAMENTO ---

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n > 0:
            st.warning("⚠️ **ANOMALIA DI TREND (INERZIA STORICA)**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** mostra un CAGR in rallentamento al **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante l'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Caso di inerzia statistica: i dati correnti (sia numero di aiuti che valore medio in crescita) indicano un mercato in salute, ma il CAGR rallenta perché confrontato con picchi storici passati eccezionali.
            """)

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n <= 0:
            st.info("📉 **RALLENTAMENTO CON CONSOLIDAMENTO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** continua a crescere al CAGR del **{cagr_att:.1f}%** ma **📉 in rallentamento** rispetto al {anno_p} ({c_pre:.1f}%).
            * Grazie al calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Dopo un'annata d'oro, il mercato target sta rallentando, spostando il baricentro su meno progetti ma più corposi.
            """)

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n > 0:
            st.info("📉 **RALLENTAMENTO CON FRAZIONAMENTO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** continua a crescere al CAGR del **{cagr_att:.1f}%** ma **📉 in rallentamento** rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Dopo un'annata d'oro, il mercato target sta rallentando puntando a fornire più aiuti ma meno corposi.
            """)

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.info("📉 **AVVISO DI CONTRAZIONE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** continua a crescere al CAGR del **{cagr_att:.1f}%** ma **📉 in rallentamento** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Fase di contrazione: il rallentamento è accompagnato da un calo sia nel numero di aiuti che nel loro valore medio.
            """)

        # --- AREA 3: CAGR NEGATIVO + RECUPERO ---

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n > 0:
            st.warning("⚠️ **RECUPERO SISTEMICO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte di un aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Segnali di ripresa: il mercato ricomincia ad aggiungere più aiuti e a maggior capitale.
            """)

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n <= 0:
            st.warning("⚠️ **RECUPERO QUALITATIVO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * Grazie al calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il calo del mercato si attenua grazie a progetti più grandi che tengono in piedi il settore nonostante la perdita di molti aiuti.
            """)

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n > 0:
            st.warning("⚠️ **RECUPERO QUANTITATIVO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato sta cercando di risollevararsi aumentando il numero di concessioni a basso costo per stimolare il settore.
            """)

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.warning("⚠️ **RIMBALZO TECNICO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il calo è meno severo, ma non ci sono spinte reali né nel valore medio né nel numero di aiuti.
            """)

        # --- AREA 4: CAGR NEGATIVO + AGGRAVAMENTO ---

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n > 0:
            st.error("🚨 **DISPERSIONE E CRISI**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Caso critico: nonostante aumentino aiuti e loro capitale il mercato target sta crollando drasticamente.
            """)

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n <= 0:
            st.error("🚨 **EROSIONE SELETTIVA**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Al calo di {abs(diff_n)} aiuti ({p_n:.1f}%) è seguito l'aumento dell'**Aiuto Medio** di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target sta crollando e sopravvivono solo pochi progetti grandi, mentre la base del mercato sta scomparendo del tutto.
            """)

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n > 0:
            st.error("🚨 **POLVERIZZAZIONE DA CRISI**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target si sta polverizzando in piccoli aiuti che non sostengono il volume economico del settore.
            """)

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.error("🚨 **RECESSIONE TOTALE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante il calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Stato di crisi massima: esaurimento dei fondi e crollo totale dell'interesse e del valore sul mercato target.
            """)

    
