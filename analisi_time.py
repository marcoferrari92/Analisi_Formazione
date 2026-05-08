import streamlit as st
import pandas as pd
import plotly.express as px

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
    
    # --- 2. GRAFICO VALORI ASSOLUTI (LOGARITMICO CON UNITÀ ESTESE) ---
    fig_line = px.line(
        df_time_plot, x='Periodo', y=['Mercato Totale', 'Settore Target'],
        color_discrete_map={"Mercato Totale": "#3498db", "Settore Target": "#e74c3c"},
        title="Evoluzione Temporale (Scala Logaritmica)",
        template="plotly_white", 
        line_shape="spline",
        log_y=True 
    )
    
    fig_line.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=50, b=50), 
        height=350,
        xaxis_title="Periodo",
        yaxis_title="Budget (€)",
        # Configurazione asse per evitare "M" o potenze di 10
        yaxis=dict(
            tickformat=",.0f",      # Forza separatore migliaia e 0 decimali (es: 10,000)
            dtick="D1",             # Forza i tick logaritmici (1, 2, 5, 10...)
            exponentformat="none",  # Disabilita 10^n
            minexponent=0           # Assicura che non usi la notazione scientifica
        )
    )
    
    
    st.plotly_chart(fig_norm, use_container_width=True, key="grafico_incidenza_percentuale")
    st.plotly_chart(fig_line, use_container_width=True, key="grafico_budget_assoluto_log")

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
