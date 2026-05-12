import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def pareto_analysis(df, guida_pareto=""):
    """
    Analisi di Pareto con scaglioni specifici: 5%, 10%, 20%, 50%, 80%, 95%.
    """
    df_targ = df[df['IS_TARGET'] == 1].copy()
    
    if df_targ.empty:
        st.warning("Nessun dato disponibile per il settore target.")
        return

    # --- 1. PREPARAZIONE DATI PARETO ---
    df_pareto = df_targ.groupby('RNA_DENOMINAZIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_pareto = df_pareto.sort_values(by='RNA_ELEMENTO_DI_AIUTO', ascending=False)
    
    total_budget = df_pareto['RNA_ELEMENTO_DI_AIUTO'].sum()
    total_aziende = len(df_pareto)
    
    df_pareto['Cumsum'] = df_pareto['RNA_ELEMENTO_DI_AIUTO'].cumsum()
    df_pareto['Percentage'] = (df_pareto['Cumsum'] / total_budget) * 100
    df_pareto['N_Aziende_Count'] = range(1, total_aziende + 1)
    
    # --- 2. DEFINIZIONE SCAGLIONI RICHIESTI ---
    scaglioni = [5, 10, 20, 50, 80, 95]
    report_data = []

    fig_pareto = go.Figure()

    # Barre (Budget individuale)
    fig_pareto.add_trace(go.Bar(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['RNA_ELEMENTO_DI_AIUTO'],
        name="Budget Singola Azienda",
        marker_color='#3498db',
        opacity=0.2,
        hoverinfo='skip'
    ))

    # Linea Pareto (Cumulata)
    fig_pareto.add_trace(go.Scatter(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['Percentage'],
        name="% Cumulata Budget",
        line=dict(color='#e74c3c', width=3),
        yaxis="y2"
    ))

    # --- 3. AGGIUNTA DINAMICA DEGLI SCAGLIONI ---
    for s in scaglioni:
        subset = df_pareto[df_pareto['Percentage'] >= s]
        if not subset.empty:
            row = subset.iloc[0]
            n_aziende = int(row['N_Aziende_Count'])
            perc_aziende = (n_aziende / total_aziende) * 100
            
            # Colore speciale per soglie di controllo (80 e 95)
            color_line = "red" if s in [80, 95] else "gray"
            dash_style = "dash" if s in [80, 95] else "dot"

            # Linea Orizzontale soglia
            fig_pareto.add_hline(
                y=s, yref="y2", 
                line_dash=dash_style, 
                line_color=color_line, 
                opacity=0.5,
                line_width=1
            )
            
            # Punto di intersezione
            fig_pareto.add_trace(go.Scatter(
                x=[n_aziende], y=[s],
                mode='markers+text',
                marker=dict(color='black', size=8, symbol='diamond'),
                text=[f"<b>{s}%</b>"],
                textposition="top left",
                yaxis="y2",
                name=f"Soglia {s}%",
                hovertext=f"Soglia {s}% raggiunta da {n_aziende} aziende ({perc_aziende:.1f}% del totale)",
                hoverinfo="text",
                showlegend=False
            ))
            
            report_data.append({
                "Target Budget (%)": f"{s}%",
                "N. Aziende": n_aziende,
                "% su Totale Aziende": f"{perc_aziende:.2f}%",
                "Budget Cumulativo (€)": f"€ {row['Cumsum']:,.0f}"
            })

    # --- 4. LAYOUT ---
    fig_pareto.update_layout(
        title="Analisi di Concentrazione a Scaglioni",
        xaxis_title="Numero di Aziende (Ordinate per Budget)",
        yaxis_title="Budget (€)",
        yaxis2=dict(
            title="% Cumulata Budget", 
            overlaying="y", 
            side="right", 
            range=[0, 105], 
            ticksuffix="%"
        ),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(l=0, r=0, t=80, b=0),
        height=600,
        template="plotly_white"
    )

    st.plotly_chart(fig_pareto, use_container_width=True, key="pareto_scaglioni_multipli")

    # --- 5. TABELLA RIASSUNTIVA ---
    st.write("### 📊 Riepilogo Concentrazione")
    st.table(pd.DataFrame(report_data))
