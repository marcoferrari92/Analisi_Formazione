import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def time_analysis(df, guida_timeline="", guida_timemap=""):
  
    """
    Renderizza l'analisi temporale con grafici di incidenza, 
    evoluzione assoluta e heatmap di stagionalità.
    """
  
    # 1. Preparazione Dati Locale (per non sporcare il DF originale fuori dalla funzione)
    df_temp = df.copy()
    df_temp['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_temp['RNA_DATA_CONCESSIONE'])
    df_temp['AnnoMonth'] = df_temp['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
    df_temp['Anno'] = df_temp['RNA_DATA_CONCESSIONE'].dt.year
    df_temp['Mese_Num'] = df_temp['RNA_DATA_CONCESSIONE'].dt.month

  
    # --- GRAFICO A AREA (ANDAMENTO MENSILE) ---
    st.write("")
    if guida_timeline:
        with st.popover("💡 Strategia"):
            st.info(guida_timeline)
    st.write("")
    
    # Aggregazione
    df_time_tot = df_temp.groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_time_targ = df_temp[df_temp['IS_TARGET'] == 1].groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    
    df_time_plot = pd.merge(df_time_tot, df_time_targ, on='AnnoMonth', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
    df_time_plot.columns = ['Periodo', 'Mercato Totale', 'Settore Target']
    df_time_plot['Quota Target (%)'] = (df_time_plot['Settore Target'] / df_time_plot['Mercato Totale'] * 100).fillna(0)
    
    # --- 1. GRAFICO INCIDENZA % ---
    fig_norm = px.area(
        df_time_plot, x='Periodo', y='Quota Target (%)',
        title="Evoluzione Temporale della Quota di Mercato del Settore Target",
        template="plotly_white", line_shape="spline", markers=True
    )
    fig_norm.update_traces(line_color='#e74c3c', fill='tozeroy')
    fig_norm.update_layout(
        yaxis_ticksuffix="%", 
        margin=dict(l=60, r=20, t=50, b=0),
        height=350
    )
    


    # --- 2. GRAFICO VALORI ASSOLUTI (RADICE QUADRATA) ---
    
    # Preparazione valori in Milioni
    df_time_plot['Mercato_Mln'] = df_time_plot['Mercato Totale'] / 1e6
    df_time_plot['Target_Mln'] = df_time_plot['Settore Target'] / 1e6

    # Creazione tracce manuali per massimo controllo su colori e nomi
    import plotly.graph_objects as go
    fig_line = go.Figure()

    # Traccia Mercato Totale (Blu)
    fig_line.add_trace(go.Scatter(
        x=df_time_plot['Periodo'], 
        y=np.sqrt(df_time_plot['Mercato_Mln']),
        name="Mercato Totale",
        line=dict(color='#3498db', width=2.5, shape='spline'),
        mode='lines'
    ))

    # Traccia Settore Target (Rosso)
    fig_line.add_trace(go.Scatter(
        x=df_time_plot['Periodo'], 
        y=np.sqrt(df_time_plot['Target_Mln']),
        name="Settore Target",
        line=dict(color='#e74c3c', width=2.5, shape='spline'),
        mode='lines'
    ))

    # Definizione dei Tick "Umani" (mostriamo valori reali su scala radice)
    max_mln = df_time_plot['Mercato_Mln'].max()
    # Generiamo tick realistici (es: 0, 1, 10, 50, 100...) adattandoli al range
    potential_ticks = np.array([0, 1, 5, 10, 25, 50, 100, 200, 400, 800])
    tick_vals = potential_ticks[potential_ticks <= max_mln]
    if max_mln not in tick_vals: tick_vals = np.append(tick_vals, max_mln)

    fig_line.update_layout(
        title="Evoluzione Temporale (Mln €) - Scala Radice Quadrata",
        template="plotly_white",
        # Legenda in alto per non disallineare l'asse X
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # Margine sinistro fissato a 80 per sincronia perfetta con il grafico sopra
        margin=dict(l=80, r=20, t=50, b=50),
        height=400,
        xaxis_title="Periodo",
        yaxis=dict(
            title="Budget (Mln €)",
            tickmode='array',
            tickvals=np.sqrt(tick_vals),
            ticktext=[f"{v:.1f}" for v in tick_vals]
        )
    )

    st.plotly_chart(fig_norm, use_container_width=True, key="grafico_incidenza_percentuale")
    st.plotly_chart(fig_line, use_container_width=True, key="grafico_assoluto_sqrt")

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
