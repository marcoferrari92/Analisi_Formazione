import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def time_analysis(df, guida_timeline="", guida_timemap=""):
    """
    Renderizza l'analisi temporale con grafici sincronizzati (Quota % e Valori Assoluti)
    e Heatmap di stagionalità.
    """
    # 1. Preparazione Dati Locale
    df_temp = df.copy()
    df_temp['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_temp['RNA_DATA_CONCESSIONE'])
    df_temp['AnnoMonth'] = df_temp['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
    df_temp['Anno'] = df_temp['RNA_DATA_CONCESSIONE'].dt.year
    df_temp['Mese_Num'] = df_temp['RNA_DATA_CONCESSIONE'].dt.month

    # Aggregazione per i grafici a linea
    df_time_tot = df_temp.groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_time_targ = df_temp[df_temp['IS_TARGET'] == 1].groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    
    df_time_plot = pd.merge(df_time_tot, df_time_targ, on='AnnoMonth', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
    df_time_plot.columns = ['Periodo', 'Mercato Totale', 'Settore Target']
    df_time_plot['Quota Target (%)'] = (df_time_plot['Settore Target'] / df_time_plot['Mercato Totale'] * 100).fillna(0)
    
    # Valori in Milioni per il grafico assoluto
    df_time_plot['Mercato_Mln'] = df_time_plot['Mercato Totale'] / 1e6
    df_time_plot['Target_Mln'] = df_time_plot['Settore Target'] / 1e6

    # --- INIZIO UI ---
    st.subheader("📈 Evoluzione del Budget nel Tempo")
    if guida_timeline:
        with st.popover("💡 Strategia"):
            st.info(guida_timeline)
    


    # --- PREPARAZIONE RANGE E TICK ASSE X ---
    x_min = df_time_plot['Periodo'].min()
    x_max = df_time_plot['Periodo'].max()
    
    # --- 1. GRAFICO QUOTA TARGET (%) ---
    fig_norm = px.area(
        df_time_plot, x='Periodo', y='Quota Target (%)',
        title="Evoluzione Temporale della Quota di Mercato del Settore Target",
        template="plotly_white", line_shape="spline", markers=True
    )
    fig_norm.update_traces(line_color='#e74c3c', fill='tozeroy', marker=dict(size=6))
    
    fig_norm.update_layout(
        yaxis_ticksuffix="%", 
        margin=dict(l=100, r=40, t=50, b=0),
        height=350,
        yaxis=dict(automargin=False, gridcolor="#f0f0f0"),
        xaxis=dict(
            range=[x_min, x_max],
            showgrid=True,
            gridcolor="#e1e1e1", # Griglia verticale più visibile
            griddash="dot",      # Rende la griglia tratteggiata
            constrain='domain',
            # SPIKELINES: Linee tratteggiate al passaggio del mouse
            showspikes=True,
            spikemode='across',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#999999'
        )
    )
    
    # --- 2. GRAFICO VALORI ASSOLUTI (RADICE QUADRATA) ---
    # ... (Codice Scatter e tick_vals rimane lo stesso) ...
    
    fig_line.update_layout(
        title="Evoluzione Temporale (Mln €) - Scala Radice Quadrata",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=100, r=40, t=50, b=50),
        height=400,
        xaxis=dict(
            title="Periodo",
            range=[x_min, x_max],
            showgrid=True,
            gridcolor="#e1e1e1", # Stessa griglia tratteggiata
            griddash="dot",
            constrain='domain',
            # SPIKELINES: Stessa configurazione per il grafico sotto
            showspikes=True,
            spikemode='across',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#999999'
        ),
        yaxis=dict(
            title="Budget (Mln €)",
            tickmode='array',
            tickvals=np.sqrt(tick_vals),
            ticktext=[f"{v:.1f}" for v in tick_vals],
            automargin=False,
            gridcolor="#f0f0f0"
        ),
        # Sincronizza il puntatore tra i grafici (Hovermode condiviso)
        hovermode="x unified" 
    )
    
    st.plotly_chart(fig_norm, use_container_width=True, key="norm_final_spike")
    st.plotly_chart(fig_line, use_container_width=True, key="line_final_spike")

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
