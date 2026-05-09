import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots 


GUIDA_TIMELINE = """ Vedi se il settore target è in crescita, in declino o se ha un andamento periodico legato a bandi stagionali"""
GUIDA_TIMEMAP = """I mesi più intensi indicano quando le aziende ricevono più liquidità. Individua i momenti migliori per proporre nuovi investimenti"""
GUIDA_CAGR = r"""
### 📈 Guida al CAGR (Compound Annual Growth Rate)

Il **CAGR** misura la crescita media annua del **Settore Target**, ipotizzando una progressione costante.

#### 🧮 La Formula
$$CAGR = \left( \frac{\text{Valore Finale}}{\text{Valore Iniziale}} \right)^{\frac{1}{n}} - 1$$

#### 💡 Come leggere i dati:
1.  **L'Anno Zero (Punto di Riferimento)**: Tutti i calcoli partono dal primo anno del dataset (es. 2020).
2.  **Il "Salto" del Primo Anno**: Nel primo anno dopo l'inizio ($n=1$), il CAGR coincide con la **crescita semplice**. Se vedi un valore molto alto (es. +36%), indica l'esplosione immediata del mercato in quell'anno.
3.  **Anni Successivi**: I valori si "ammorbidiscono" perché la crescita totale viene spalmata (composta) su più anni rispetto all'anno zero.

**Esempio:** Un CAGR del 10% su 3 anni significa che, partendo dal valore iniziale, il settore è cresciuto mediamente del 10% ogni anno per tre anni di fila.
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


    # --- 1. Calcolo Concentrazione Annuale Evoluta ---
    st.divider()
    st.subheader("📊 Analisi Storica e CAGR (Settore Target)")
    
    st.write("")
    with st.popover("💡 Strategia"):
        st.info(GUIDA_CAGR)

    # Raggruppamento base
    df_annual = df_temp.groupby('Anno').agg(
        Aiuti_Tot=('RNA_ELEMENTO_DI_AIUTO', 'count'),
        Aiuti_Target=('IS_TARGET', 'sum'),
        Vol_Tot=('RNA_ELEMENTO_DI_AIUTO', 'sum'),
        Vol_Target=('RNA_ELEMENTO_DI_AIUTO', lambda x: df_temp.loc[x.index, 'RNA_ELEMENTO_DI_AIUTO'][df_temp['IS_TARGET'] == 1].sum())
    ).reset_index().sort_values('Anno')

    # Funzione CAGR sicura
    def calc_cagr(current_val, start_val, current_year, start_year):
        n_anni = current_year - start_year
        if n_anni <= 0 or start_val <= 0 or current_val <= 0:
            return 0.0
        return (current_val / start_val) ** (1 / n_anni) - 1

    # Punti di partenza Target
    anno_start = df_annual['Anno'].min()
    prat_target_start = df_annual['Aiuti_Target'].iloc[0] 
    vol_target_start = df_annual['Vol_Target'].iloc[0]

    # --- 2. Calcolo Quote e CAGR ---
    df_annual['Quota Target (%)'] = (df_annual['Aiuti_Target'] / df_annual['Aiuti_Tot'] * 100).fillna(0)
    df_annual['Quota Vol. Target (%)'] = (df_annual['Vol_Target'] / df_annual['Vol_Tot'] * 100).fillna(0)
    
    df_annual['CAGR Target'] = df_annual.apply(
        lambda x: calc_cagr(x['Aiuti_Target'], prat_target_start, x['Anno'], anno_start) * 100, axis=1
    )
    df_annual['CAGR Vol. Target'] = df_annual.apply(
        lambda x: calc_cagr(x['Vol_Target'], vol_target_start, x['Anno'], anno_start) * 100, axis=1
    )

    # --- 3. Formattazione Volumi (Sintetica per leggibilità) ---
    df_view = df_annual.sort_values('Anno', ascending=False).copy()
    
    # Prepariamo le colonne volume in formato "1.2M €"
    df_view['Vol_Tot_Fmt'] = df_view['Vol_Tot'].apply(lambda x: f"€ {x/1e6:.2f}M")
    df_view['Vol_Target_Fmt'] = df_view['Vol_Target'].apply(lambda x: f"€ {x/1e6:.2f}M")

    # Selezione Colonne Finale (Ordine richiesto)
    df_final = df_view[[
        'Anno', 
        'Aiuti_Tot', 
        'Aiuti_Target', 
        'Quota Target (%)', 
        'CAGR Target',
        'Vol_Tot_Fmt', 
        'Vol_Target_Fmt', 
        'Quota Vol. Target (%)', 
        'CAGR Vol. Target'
    ]].copy()

    # Rinomina Colonne
    df_final.columns = [
        'Anno', 'Aiuti Tot.', 'Aiuti Target', 'Quota Target (%)', 'CAGR Target',
        'Vol. Tot. (€)', 'Vol. Target (€)', 'Quota Vol. Target (%)', 'CAGR Vol. Target'
    ]

    # --- 4. Rendering Tabella ---
    st.dataframe(
        df_final,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Anno": st.column_config.NumberColumn("Anno", format="%d"),
            "Aiuti Tot.": st.column_config.NumberColumn("Aiuti Tot.", format="%d"),
            "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d"),
            "Quota Target (%)": st.column_config.NumberColumn("Quota Target (%)", format="%.2f %%"),
            "CAGR Target": st.column_config.NumberColumn("CAGR Target", format="%.2f %%"),
            "Vol. Tot. (€)": st.column_config.TextColumn("Vol. Tot. (€)"),
            "Vol. Target (€)": st.column_config.TextColumn("Vol. Target (€)"),
            "Quota Vol. Target (%)": st.column_config.NumberColumn("Quota Vol. Target (%)", format="%.2f %%"),
            "CAGR Vol. Target": st.column_config.NumberColumn("CAGR Vol. Target", format="%.2f %%")
        }
    )
