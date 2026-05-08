import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def time_analysis(df, guida_timeline="", guida_timemap=""):
    # 1. Preparazione Dati
    df_temp = df.copy()
    df_temp['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_temp['RNA_DATA_CONCESSIONE'])
    df_temp['AnnoMonth'] = df_temp['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
    
    # Aggregazione
    df_time_tot = df_temp.groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_time_targ = df_temp[df_temp['IS_TARGET'] == 1].groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    
    df_time_plot = pd.merge(df_time_tot, df_time_targ, on='AnnoMonth', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
    df_time_plot.columns = ['Periodo', 'Mercato Totale', 'Settore Target']
    
    # Calcoli per i grafici
    df_time_plot['Quota Target (%)'] = (df_time_plot['Settore Target'] / df_time_plot['Mercato Totale'] * 100).fillna(0)
    df_time_plot['Mercato_Mln'] = df_time_plot['Mercato Totale'] / 1e6
    df_time_plot['Target_Mln'] = df_time_plot['Settore Target'] / 1e6

    # Range per sincronizzare perfettamente l'asse X
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
        margin=dict(l=100, r=40, t=50, b=0),
        height=350,
        yaxis=dict(ticksuffix="%", automargin=False, gridcolor="#f0f0f0"),
        xaxis=dict(
            range=[x_min, x_max],
            showgrid=True,
            gridcolor="#e1e1e1",
            griddash="dot",
            showspikes=True,
            spikemode='across',
            spikedash='dash',
            spikecolor='#999999',
            constrain='domain'
        ),
        hovermode="x unified"
    )

    # --- 2. GRAFICO VALORI ASSOLUTI (RADICE QUADRATA) ---
    # Creazione esplicita della variabile fig_line
    fig_line = go.Figure()
    
    # Traccia Totale
    fig_line.add_trace(go.Scatter(
        x=df_time_plot['Periodo'], 
        y=np.sqrt(df_time_plot['Mercato_Mln']),
        name="Mercato Totale",
        line=dict(color='#3498db', width=2, shape='spline'),
        mode='lines+markers',
        marker=dict(size=6)
    ))
    
    # Traccia Target
    fig_line.add_trace(go.Scatter(
        x=df_time_plot['Periodo'], 
        y=np.sqrt(df_time_plot['Target_Mln']),
        name="Settore Target",
        line=dict(color='#e74c3c', width=2, shape='spline'),
        mode='lines+markers',
        marker=dict(size=6)
    ))

    # Calcolo Tick asse Y
    max_mln = df_time_plot['Mercato_Mln'].max()
    potential_ticks = np.array([0, 1, 5, 10, 25, 50, 100, 200, 400, 800])
    tick_vals = potential_ticks[potential_ticks <= max_mln]
    if max_mln not in tick_vals: tick_vals = np.append(tick_vals, max_mln)

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
            gridcolor="#e1e1e1",
            griddash="dot",
            showspikes=True,
            spikemode='across',
            spikedash='dash',
            spikecolor='#999999',
            constrain='domain'
        ),
        yaxis=dict(
            title="Budget (Mln €)",
            tickmode='array',
            tickvals=np.sqrt(tick_vals),
            ticktext=[f"{v:.1f}" for v in tick_vals],
            automargin=False,
            gridcolor="#f0f0f0"
        ),
        hovermode="x unified"
    )

    # Rendering
    st.plotly_chart(fig_norm, use_container_width=True, key="norm_final")
    st.plotly_chart(fig_line, use_container_width=True, key="line_final")
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
