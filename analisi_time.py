import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots 
import datetime as dt
import plotly.figure_factory as ff


GUIDA_TIMELINE = """ Vedi se il settore target è in crescita, in declino o se ha un andamento periodico legato a bandi stagionali"""
GUIDA_TIMEMAP = """ Periodi che si ripetono come i più intensi (vincitori) in più annate, e che hanno anche un budget medio annuo più alto, potrebbero indicare un trend nell'ingresso di liquidità delle aziendeda per il settore target. 
                    Potrebbe essere utile attivare le campagne marketing nei mesi subiti precedenti"""
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
    df_temp = df_temp[df_temp['RNA_ELEMENTO_DI_AIUTO'] > 0].copy()
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
    

  
    # *******************
    # HEATMAP STAGIONALE 
    # *******************
  
    st.divider()
    st.write("")
    st.subheader("🔥 Intensità degli Aiuti Target per Mese e Anno")
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

    # --- ANALISI DINAMICA DELLE FINESTRE TEMPORALI ---
    # Layout
    col0, col1, col2, col3, col4 = st.columns([0.3, 1.3, 0.3, 2.3, 0.3])

    anno_attuale = dt.datetime.now().year
    df_clean = df_temp[(df_temp['IS_TARGET'] == 1) & (df_temp['Anno'] < anno_attuale)].copy()
    
    if not df_clean.empty:
        with col1:
            window_size = st.slider("Ampiezza finestra (mesi):", min_value=1, max_value=12, value=4, key="slider_vincitori")
            with st.popover("💡 Strategia"):
              st.info(GUIDA_TIMEMAP)
      
        # Logica di calcolo (identica alla precedente)
        df_m_y = df_clean.groupby(['Anno', 'Mese_Num'])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
        budget_totale_storico = df_clean['RNA_ELEMENTO_DI_AIUTO'].sum()
          
        rolling_data = []
        for i in range(1, 13):
            mesi_w = []
            nomi_mesi_w = []
            for offset in range(window_size):
                m = i + offset
                if m > 12: m -= 12
                mesi_w.append(m)
                nomi_mesi_w.append(mesi_ita[m])
            
            nome_w = nomi_mesi_w[0] if window_size == 1 else f"{nomi_mesi_w[0]}-{nomi_mesi_w[-1]}"
            for anno in df_m_y['Anno'].unique():
                valore = df_m_y[(df_m_y['Anno'] == anno) & (df_m_y['Mese_Num'].isin(mesi_w))]['RNA_ELEMENTO_DI_AIUTO'].sum()
                rolling_data.append({'Anno': int(anno), 'Finestra': nome_w, 'Budget': valore})

        df_rolling_all = pd.DataFrame(rolling_data)

        # Metriche e Vincitori
        stats_w = df_rolling_all.groupby('Finestra')['Budget'].agg(['mean', 'sum']).reset_index()
        stats_w.columns = ['Finestra', 'Budget Medio (€)', 'Somma Totale']
        stats_w['Quota sul Totale %'] = (stats_w['Somma Totale'] / budget_totale_storico) * 100

        idx_max = df_rolling_all.groupby('Anno')['Budget'].idxmax()
        vincitori_annuali = df_rolling_all.loc[idx_max]
        
        vittorie = vincitori_annuali['Finestra'].value_counts().reset_index()
        vittorie.columns = ['Finestra', 'Vittorie']
        
        anni_vittoria = vincitori_annuali.groupby('Finestra')['Anno'].apply(lambda x: ', '.join(map(str, sorted(x, reverse=True)))).reset_index()
        anni_vittoria.columns = ['Finestra', 'Anni Vittoria']

        # Unione e FILTRO CRUCIALE
        classifica_finale = stats_w.merge(vittorie, on='Finestra', how='inner') # 'inner' tiene solo chi ha vinto
        classifica_finale = classifica_finale.merge(anni_vittoria, on='Finestra', how='left')
        
        classifica_finale = classifica_finale.sort_values(['Vittorie', 'Budget Medio (€)'], ascending=False)

        with col3:
            if not classifica_finale.empty:
                st.write(f"**Periodi Hot (Finestre di {window_size} mesi)**")
                st.dataframe(
                    classifica_finale[['Finestra', 'Vittorie', 'Anni Vittoria', 'Budget Medio (€)', 'Quota sul Totale %']].style.format({
                        'Budget Medio (€)': '{:,.0f} €',
                        'Quota sul Totale %': '{:.2f} %'
                    }).background_gradient(cmap='YlOrRd', subset=['Quota sul Totale %', 'Vittorie']),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.error("Nessuna finestra ha vinto in modo chiaro. Prova a cambiare l'ampiezza dello slider.")

    else:
        st.warning("Dati insufficienti negli anni conclusi.")



    
    # ***********************
    # ANALISI STORICA (CAGR)
    # ***********************
  
    st.divider()
    st.write("")
    st.subheader("📈 Analisi Storica: Aiuto Medio vs Crescita Composta")
    st.write("")
    with st.popover("💡 Strategia"):
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

    # --- TABELLA DETTAGLIATA ---

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
            * **Significato:** Fase di contrazione: il rallentamento del mercato target è accompagnato da un calo sia nel numero di aiuti che nel loro valore medio.
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

# ***********************
    # FREQUENZE AIUTI TARGET 
    # ***********************

    # Calcolo Freq. Aiuti
    # Diff. tra primo e ultimo aiuto normalizzato per (N-1) con N numero aiuti totali. 
    # Si usa (N - 1) perché la frequenza non misura il numero di eventi, 
    # ma la durata media degli INTERVALLI tra di essi.
    # -> Il primo aiuto è il 'punto zero' e non ha un'attesa precedente.
    # -> Se N=1, il risultato è 0 (nessuna ricorrenza possibile con un solo evento).

    st.divider()
    st.subheader("🏢 Frequenze di Aiuti")
    
    # 1. Metriche TOTALI
    analisi_tot = df_temp.groupby('CF_TROVATO').agg({
        'CF_TROVATO': 'count',
        'RNA_DATA_CONCESSIONE': ['min', 'max']
    })
    analisi_tot.columns = ['N° Aiuti Tot', 'Primo Aiuto', 'Ultimo Aiuto']
    analisi_tot = analisi_tot.reset_index()
    
    # Calcolo Freq. Aiuti Totale
    diff_date_tot = (analisi_tot['Ultimo Aiuto'] - analisi_tot['Primo Aiuto']).dt.days
    analisi_tot['Freq. Aiuti'] = diff_date_tot / (analisi_tot['N° Aiuti Tot'] - 1)
    analisi_tot['Freq. Aiuti'] = analisi_tot['Freq. Aiuti'].replace([float('inf'), -float('inf')], pd.NA)

    # 2. Metriche settore TARGET
    df_target = df_temp[df_temp['IS_TARGET'] == 1].copy()
    
    if not df_target.empty:
        analisi_target = df_target.groupby('CF_TROVATO').agg({
            'RAGIONE SOCIALE': 'first',
            'RNA_ELEMENTO_DI_AIUTO': 'sum',
            'CF_TROVATO': 'count',
            'RNA_DATA_CONCESSIONE': ['min', 'max']
        })
        analisi_target.columns = ['Ragione Sociale', 'Budget Target (€)', 'N° Aiuti Target', 'Primo Target', 'Ultimo Target']
        analisi_target = analisi_target.reset_index()
        
        oggi_dt = dt.datetime.now()
        # Giorni dall'ultimo aiuto target (Recency)
        analisi_target['Ultimo Target (gg)'] = (oggi_dt - analisi_target['Ultimo Target']).dt.days
        
        # Freq. Aiuti Target
        diff_date_target = (analisi_target['Ultimo Target'] - analisi_target['Primo Target']).dt.days
        analisi_target['Freq. Aiuti Target'] = diff_date_target / (analisi_target['N° Aiuti Target'] - 1)
        analisi_target['Freq. Aiuti Target'] = analisi_target['Freq. Aiuti Target'].replace([float('inf'), -float('inf')], pd.NA)

        # 3. Merge e Creazione colonna composta "Aiuti Target (%)"
        analisi_finale = analisi_target.merge(analisi_tot[['CF_TROVATO', 'N° Aiuti Tot', 'Freq. Aiuti']], on='CF_TROVATO', how='left')
        
        analisi_finale['Quota %'] = (analisi_finale['N° Aiuti Target'] / analisi_finale['N° Aiuti Tot']) * 100
        analisi_finale['Aiuti Target (%)'] = analisi_finale.apply(lambda x: f"{int(x['N° Aiuti Target'])} ({x['Quota %']:.1f}%)", axis=1)

        # --- 4. CALCOLO VIVACITÀ COMPOSTA (TARGET + GENERALE) ---
        analisi_finale.rename(columns={
            'CF_TROVATO': 'P.IVA', 
            'Freq. Aiuti': 'Freq. Aiuti (gg)', 
            'Freq. Aiuti Target': 'Freq. Aiuti Target (gg)'
        }, inplace=True)
        
        # A. Calcoliamo la Recency Totale (giorni dall'ultimo aiuto qualunque)
        oggi_dt = dt.datetime.now()
        analisi_tot['Recency Totale'] = (oggi_dt - analisi_tot['Ultimo Aiuto']).dt.days
        
        # B. Portiamo la Recency Totale nel DataFrame finale
        analisi_finale = analisi_finale.merge(analisi_tot[['CF_TROVATO', 'Recency Totale']], left_on='P.IVA', right_on='CF_TROVATO', how='left')

        # C. Calcolo soglie statistiche (Quartili) per entrambi i mondi
        # Target
        q1_t = analisi_finale['Freq. Aiuti Target (gg)'].quantile(0.25)
        med_t = analisi_finale['Freq. Aiuti Target (gg)'].median()
        q3_t = analisi_finale['Freq. Aiuti Target (gg)'].quantile(0.75)
        
        # Generale (basato sulla Recency Totale della popolazione)
        q1_g = analisi_finale['Recency Totale'].quantile(0.25)
        med_g = analisi_finale['Recency Totale'].median()
        q3_g = analisi_finale['Recency Totale'].quantile(0.75)

        def definisci_vivacita_doppia(row):
            # Caso base
            if row['N° Aiuti Target'] <= 1: 
                return "🌱 OCCASIONALE"
            
            # 1. Valutazione GENERALE
            rec_g = row['Recency Totale']
            if rec_g <= q1_g: stato_g = "IPERATTIVA"
            elif rec_g <= med_g: stato_g = "VIVA"
            elif rec_g <= q3_g: stato_g = "STANCA"
            else: stato_g = "MORENTE"
            
            # 2. Valutazione TARGET
            rec_t = row['Ultimo Target (gg)']
            if rec_t <= q1_t: stato_t = "FEDELE"
            elif rec_t <= med_t: stato_t = "INTERESSATA"
            elif rec_t <= q3_t: stato_t = "DISTRATTA"
            else: stato_t = "DISINTERESSATA"
            
            return f"{stato_g} - {stato_t}"

        analisi_finale['Vivacità'] = analisi_finale.apply(definisci_vivacita_doppia, axis=1)

        # --- 5. VISUALIZZAZIONE: METRICHE PRINCIPALI (KPI) ---
        st.write("")
        col0, col1, col2, col3, col4, col5 = st.columns(6)
        
        # Calcolo delle mediane per i KPI
        m_aiuti_tot = analisi_finale['N° Aiuti Tot'].median()
        m_aiuti_target = analisi_finale['N° Aiuti Target'].median()
        m_freq_tot = analisi_finale['Freq. Aiuti (gg)'].median()
        m_freq_target = analisi_finale['Freq. Aiuti Target (gg)'].median()

        with col1:
            st.metric("Mediana Aiuti Totali", f"{m_aiuti_tot:.0f}")
        with col2:
            st.metric("Mediana Aiuti Target", f"{m_aiuti_target:.0f}")
        with col3:
            st.metric("Mediana Freq. Aiuti", f"{m_freq_tot:.0f} gg")
        with col4:
            st.metric("Mediana Freq. Target", f"{m_freq_target:.0f} gg")

        # --- 6. VISUALIZZAZIONE: GRAFICI STATISTICI ---
        df_stats = analisi_finale.dropna(subset=['Freq. Aiuti (gg)', 'Freq. Aiuti Target (gg)']).copy()

        if not df_stats.empty:
            fig_combined = px.histogram(
                df_stats, 
                x=["Freq. Aiuti (gg)", "Freq. Aiuti Target (gg)"],
                marginal="box",
                barmode='overlay',
                nbins=50,
                title="Distribuzione e Dispersione Frequenze (Totale vs Target)",
                labels={'value': 'Giorni tra gli aiuti', 'variable': 'Tipo Frequenza'},
                color_discrete_map={"Freq. Aiuti (gg)": "#1f77b4", "Freq. Aiuti Target (gg)": "#FF0000"},
                opacity=0.6,
                height=800,
                hover_data={
                    "Ragione Sociale": True,
                    "Budget Target (€)": ":,.0f"
                }
            )
            
            hovertemplate_dots = (
                "<b>%{customdata[0]}</b><br>" +
                "Frequenza: %{x:.0f} gg<br>" +
                "Budget Target: %{customdata[1]:,.0f} €" +
                "<extra></extra>"
            )
            
            fig_combined.update_layout(
                yaxis=dict(domain=[0, 0.5]),      
                yaxis2=dict(domain=[0.55, 1]),   
                xaxis_title="Giorni",
                yaxis_title="Numero di Aziende",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                bargap=0.01
            )
            
            fig_combined.update_traces(
                boxpoints='all', 
                pointpos=0, 
                jitter=1, 
                marker=dict(size=4),
                hovertemplate=hovertemplate_dots,
                selector=dict(type='box') 
            )
            st.plotly_chart(fig_combined, use_container_width=True)
        else:
            st.warning("Dati insufficienti per generare i grafici statistici.")

        # --- 7. TABELLA CON STILE AGGIORNATO ---
        
        # Definiamo esplicitamente le colonne da mostrare per evitare l'errore "name not defined"
        colonne_finali = [
            'P.IVA', 
            'Ragione Sociale', 
            'Budget Target (€)', 
            'Aiuti Target (%)', 
            'Ultimo Target (gg)', 
            'Vivacità', 
            'Vivacità Target'
        ]

        def style_vivacita_doppia(val):
            if not isinstance(val, str): return ""
            if "OCCASIONALE" in val: return 'color: #95a5a6;'
            
            style = 'font-weight: bold;'
            # Colori per la colonna GENERALE (Vivacità)
            if "IPERATTIVA" in val: style += ' color: #1b5e20; background-color: #e8f5e9;'
            elif "VIVA" in val: style += ' color: #2ecc71;'
            elif "STANCA" in val: style += ' color: #f39c12;'
            elif "MORENTE" in val: style += ' color: #e74c3c; opacity: 0.8;'
            
            # Colori per la colonna TARGET (Vivacità Target)
            if "FEDELE" in val: style += ' color: #2e7d32; border-left: 3px solid #2e7d32;'
            elif "INTERESSATA" in val: style += ' color: #2ecc71;'
            elif "DISTRATTA" in val: style += ' color: #f39c12;'
            elif "DISINTERESSATA" in val: style += ' color: #e74c3c; background-color: #ffebee;'
            
            return style

        # Visualizzazione Tabella
        st.write("---")
        st.write("**🏢 Ranking Strategico: Stato Generale vs Focus Target**")
        
        # Usiamo .map() per applicare lo stile alle due colonne di vivacità
        st.dataframe(
            analisi_finale[colonne_finali].sort_values('Ultimo Target (gg)').style.format({
                'Budget Target (€)': '{:,.0f} €',
                'Ultimo Target (gg)': '{:.0f} gg'
            }).map(style_vivacita_doppia, subset=['Vivacità', 'Vivacità Target'])
            .background_gradient(cmap='RdYlGn_r', subset=['Ultimo Target (gg)']),
            use_container_width=True, hide_index=True
        )

        
    

