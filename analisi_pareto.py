import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def pareto_analysis(df, guida_pareto=""):
    """
    Renderizza la Top 10 dei beneficiari e l'analisi di concentrazione di Pareto.
    """
    # Filtro dati per settore target
    df_targ = df[df['IS_TARGET'] == 1].copy()
    
    if df_targ.empty:
        st.warning("Nessun dato disponibile per il settore target in questa sezione.")
        return

    # --- 1. PREPARAZIONE DATI: TOP 10 BENEFICIARI ---
    df_top_10 = df_targ.groupby('RNA_DENOMINAZIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_top_10 = df_top_10.sort_values(by='RNA_ELEMENTO_DI_AIUTO', ascending=False).head(10)

    # --- BAR CHART ORIZZONTALE (TOP 10) ---
    st.subheader("🔝 Top 10 Player del Settore Target")
    
    fig_top = px.bar(
        df_top_10,
        x='RNA_ELEMENTO_DI_AIUTO',
        y='RNA_DENOMINAZIONE_BENEFICIARIO',
        orientation='h',
        text_auto='.2s',
        color='RNA_ELEMENTO_DI_AIUTO',
        color_continuous_scale='Reds',
        labels={'RNA_ELEMENTO_DI_AIUTO': 'Budget Target Totale (€)', 'RNA_DENOMINAZIONE_BENEFICIARIO': 'Azienda'}
    )
    
    fig_top.update_layout(
        yaxis={'categoryorder': 'total ascending'}, 
        coloraxis_showscale=False,
        margin=dict(l=0, r=20, t=30, b=0),
        height=450
    )
    st.plotly_chart(fig_top, use_container_width=True, key="bar_top_10")

    

    # --- 2. ANALISI DI PARETO (80/20) ---
    st.divider()
    st.subheader("📉 Concentrazione Mercato Target (Curva di Pareto)")
    
    if guida_pareto:
        st.write("")
        with st.pophover("📖 Metodologia"):
            st.markdown(guida_pareto)

    # Preparazione dati Pareto
    df_pareto = df_targ.groupby('RNA_DENOMINAZIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_pareto = df_pareto.sort_values(by='RNA_ELEMENTO_DI_AIUTO', ascending=False)
    
    df_pareto['Cumsum'] = df_pareto['RNA_ELEMENTO_DI_AIUTO'].cumsum()
    total_budget = df_pareto['RNA_ELEMENTO_DI_AIUTO'].sum()
    df_pareto['Percentage'] = (df_pareto['Cumsum'] / total_budget) * 100
    df_pareto['N_Aziende_Count'] = range(1, len(df_pareto) + 1)
    
    # Trova il punto di intersezione per l'80%
    intersezione = df_pareto[df_pareto['Percentage'] >= 80].iloc[0]
    x_intersezione = intersezione['N_Aziende_Count']
                    
    fig_pareto = go.Figure()
    
    # Barre: Budget per singola azienda
    fig_pareto.add_trace(go.Bar(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['RNA_ELEMENTO_DI_AIUTO'],
        name="Budget Azienda",
        marker_color='#3498db',
        opacity=0.4
    ))
    
    # Linea: Percentuale cumulata
    fig_pareto.add_trace(go.Scatter(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['Percentage'],
        name="% Cumulata Budget Target",
        line=dict(color='#e74c3c', width=3),
        yaxis="y2"
    ))
    
    # Retta Orizzontale (Soglia 80%)
    fig_pareto.add_hline(
        y=80, yref="y2", 
        line_dash="dash", line_color="gray", 
        annotation_text="Soglia 80%", annotation_position="top left"
    )
    
    # Retta Verticale (Punto di caduta su Asse X)
    fig_pareto.add_vline(
        x=x_intersezione, 
        line_dash="dot", line_color="black", line_width=2,
        annotation_text=f" {int(x_intersezione)} Aziende", 
        annotation_position="top right"
    )
    
    # Punto di intersezione
    fig_pareto.add_trace(go.Scatter(
        x=[x_intersezione], y=[80],
        mode='markers',
        marker=dict(color='black', size=10, symbol='circle'),
        yaxis="y2",
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig_pareto.update_layout(
        xaxis_title="Numero di Aziende (Ordinate per Budget Target)",
        yaxis_title="Budget Target della Singola Azienda (€)",
        yaxis2=dict(title="% Cumulata del Budget Target", overlaying="y", side="right", range=[0, 105], ticksuffix="%"),
        legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"),
        margin=dict(l=0, r=0, t=60, b=0),
        height=550,
        template="plotly_white"
    )
    
    st.plotly_chart(fig_pareto, use_container_width=True, key="pareto_intersezione")
