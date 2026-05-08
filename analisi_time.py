import plotly.express as px
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
    st.write("")
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


    # --- 1. Calcolo Concentrazione Annuale ---
    st.subheader("📊 Concentrazione Annuale del Budget")
    
    # Raggruppamento per anno
    df_annual = df_temp.groupby('Anno').agg({
        'RNA_ELEMENTO_DI_AIUTO': 'sum',
        'IS_TARGET': 'sum' 
    }).reset_index()
    
    # Ordiniamo per anno decrescente per la tabella
    df_annual_table = df_annual.sort_values('Anno', ascending=False).copy()
    df_annual_table.columns = ['Anno', 'Budget Totale (€)', 'Pratiche Target']

    # Calcolo dell'anno record
    idx_max = df_annual['RNA_ELEMENTO_DI_AIUTO'].idxmax()
    anno_record = df_annual.loc[idx_max]
    
    # Layout con Metriche e Tabella
    col_metrics, col_table = st.columns([1, 1])

    with col_metrics:
        st.metric(
            "Anno Record (Volume)", 
            f"{int(anno_record['Anno'])}", 
            f"€ {anno_record['RNA_ELEMENTO_DI_AIUTO']/1e6:.1f} Mln"
        )
        
        if len(df_annual) > 1:
            v_final = df_annual['RNA_ELEMENTO_DI_AIUTO'].iloc[-1]
            v_start = df_annual['RNA_ELEMENTO_DI_AIUTO'].iloc[0]
            n_anni = len(df_annual) - 1
            cagr = ((v_final / v_start)**(1/n_anni) - 1) * 100
            st.metric("CAGR Mercato", f"{cagr:.1f}%")

    with col_table:
        st.dataframe(
            df_annual_table,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Anno": st.column_config.NumberColumn(format="%d"),
                "Budget Totale (€)": st.column_config.NumberColumn(format="€ %,.0f"),
                "Pratiche Target": st.column_config.NumberColumn(format="%d")
            }
        )
