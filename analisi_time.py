import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Import fondamentale

def time_analysis(df, guida_timeline="", guida_timemap=""):
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
    st.subheader("📈 Evoluzione Temporale del Settore Target")
    if guida_timeline:
        with st.popover("💡 Strategia"):
            st.info(guida_timeline)
    
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

    # --- C. CONFIGURAZIONE LAYOUT E ASSI (Versione Linea Continua) ---
    
    # Tick asse Y inferiore
    max_mln = df_time_plot['Mercato_Mln'].max()
    potential_ticks = np.array([0, 1, 5, 10, 25, 50, 100, 200, 400, 800])
    tick_vals = potential_ticks[potential_ticks <= max_mln]
    if max_mln not in tick_vals: tick_vals = np.append(tick_vals, max_mln)

    fig.update_layout(
        template="plotly_white",
        height=750,
        margin=dict(l=100, r=40, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", # Questo unifica i tooltip
    )

    # CONFIGURAZIONE COMUNE ASSI X (Fondamentale ripetere per entrambi)
    # Creiamo un dizionario di stile per non sbagliare
    spike_style = dict(
        showspikes=True,
        spikemode='across',   # 'across' deve essere attivo su entrambi
        spikesnap='cursor',   # Forza la linea a seguire il mouse, non i punti
        spikethickness=1,
        spikedash='dash',
        spikecolor='#333333',
        showline=True,
        range=[x_min, x_max],
        constrain='domain',
        gridcolor="#e1e1e1",
        griddash="dot"
    )

    # Applichiamo lo stile al primo asse (Sopra)
    fig.update_xaxes(spike_style, row=1, col=1)
    
    # Applichiamo lo stile al secondo asse (Sotto)
    fig.update_xaxes(spike_style, row=2, col=1)
    
    # Specifichiamo i titoli degli assi singolarmente
    fig.update_xaxes(title_text="", row=1, col=1)
    fig.update_xaxes(title_text="Periodo", row=2, col=1)

    # Configurazione Assi Y
    fig.update_yaxes(
        title_text="Quota Target (%)", ticksuffix="%", 
        automargin=False, gridcolor="#f0f0f0", row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Budget (Mln €)", 
        tickmode='array',
        tickvals=np.sqrt(tick_vals),
        ticktext=[f"{v:.1f}" for v in tick_vals],
        automargin=False, gridcolor="#f0f0f0", row=2, col=1
    )

    st.plotly_chart(fig, use_container_width=True, key="temporal_subplots_v3")

    # --- 3. HEATMAP (STAGIONALITÀ) - Invariata e separata ---
    # ... (Codice Heatmap qui sotto come prima) ...
    
    st.divider()

  
    # --- HEATMAP (STAGIONALITÀ) ---
    st.subheader("🔥 Intensità delle Concessioni per Mese e Anno")
    if guida_timemap:
        with st.popover("💡 Strategia"):
            st.info(guida_timemap)
              
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
