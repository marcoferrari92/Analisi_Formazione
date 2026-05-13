import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def pareto_analysis(df, guida_pareto=""):
    """
    Analisi di Pareto con scaglioni specifici e classificazione Status Economico.
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

    # --- 2. ASSEGNAZIONE STATUS ECONOMICO ---
    def classify_status_and_color(p):
        # L'ordine è fondamentale: dal più piccolo al più grande
        if p <= 5: 
            return "Top 5%", "#e74c3c"   # Rosso (Elite)
        elif p <= 10: 
            return "Top 10%", "#e74c3c"  # Rosso
        elif p <= 20: 
            return "Top 20%", "#e74c3c"  # Rosso
        elif p <= 50: 
            return "Top 50%", "#f1c40f"  # Giallo
        elif p <= 80: 
            return "Top 80%", "#2ecc71"  # Verde
        elif p <= 95: 
            return "Top 95%", "#2ecc71"  # Verde
        else: 
            return "Oltre 95%", "#3498db" # Blu
    
    # Applicazione al DataFrame
    res = df_pareto['Percentage'].apply(classify_status_and_color)
    df_pareto['Status Economico'] = [x[0] for x in res]
    df_pareto['color_marker'] = [x[1] for x in res]

    # --- 2. LOGICA DI CLASSIFICAZIONE E COLORI ---
    def get_color_and_status(p):
        if p <= 20:
            return '#e74c3c', "Top 20%"   # Rosso
        elif p <= 50:
            return '#f1c40f', "Top 50%"   # Giallo
        elif p <= 95:
            return '#2ecc71', "Top 95%"   # Verde
        else:
            return '#3498db', "Oltre 95%" # Blu

    # Applichiamo le classificazioni
    res = df_pareto['Percentage'].apply(get_color_and_status)
    df_pareto['color_marker'] = [x[0] for x in res]

    # --- 3. LOGICA GRAFICA E SCAGLIONI ---
    scaglioni = [5, 10, 20, 50, 80, 95]
    report_data = []
    fig_pareto = go.Figure()

    # Barre (Colorate per Status Economico)
    # Usiamo colori diversi per evidenziare i vari scaglioni nel grafico a barre
    fig_pareto.add_trace(go.Bar(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['RNA_ELEMENTO_DI_AIUTO'],
        marker_color=df_pareto['color_marker'],
        name="Budget Azienda",
        opacity=1,
        customdata=df_pareto['Status Economico'],
        hovertemplate="<b>%{customdata}</b><br>Budget: %{y:,.2f}€<extra></extra>"
    ))

    # Linea Pareto
    fig_pareto.add_trace(go.Scatter(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['Percentage'],
        name="% Cumulata",
        line=dict(color='#2c3e50', width=3),
        yaxis="y2"
    ))

    for s in scaglioni:
        subset = df_pareto[df_pareto['Percentage'] >= s]
        if not subset.empty:
            row = subset.iloc[0]
            n_aziende = int(row['N_Aziende_Count'])
            perc_aziende = (n_aziende / total_aziende) * 100

            fig_pareto.add_hline(y=s, yref="y2", line_dash="dash", line_color="red", opacity=0.3)
            
            fig_pareto.add_trace(go.Scatter(
                x=[n_aziende], y=[s],
                mode='markers+text',
                marker=dict(color='black', size=8, symbol='diamond'),
                text=[f"<b>{s}%</b>"], textposition="top left",
                yaxis="y2", showlegend=False
            ))
            
            report_data.append({
                "Status Economico": f"Fino a {s}%",
                "N. Aziende": n_aziende,
                "% su Totale Aziende": f"{perc_aziende:.2f}%",
                "Budget Cumulativo": f"€ {row['Cumsum']:,.0f}"
            })

    # --- 4. LAYOUT ---
    fig_pareto.update_layout(
        title="Analisi Pareto (Scala Logaritmica per il Budget)",
        xaxis_title="Numero Aziende",
        # Configurazione asse Y logaritmico
        yaxis=dict(
            title="Budget Target (€)",
            type="log", 
            dtick=1, 
            exponentformat="SI"
        ),
        yaxis2=dict(
            title="% Cumulata",
            overlaying="y",
            side="right",
            range=[0, 105],
            ticksuffix="%"
        ),
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig_pareto, use_container_width=True)

    # --- 5. VISUALIZZAZIONE RISULTATI ---
    st.write("")
    st.write("")
    st.table(pd.DataFrame(report_data))
    st.write("")

    # Mostriamo le prime righe del dataframe arricchito
    with st.expander("🔍 Visualizza Dettaglio Aziende e Status"):
        st.dataframe(df_pareto[['RNA_DENOMINAZIONE_BENEFICIARIO', 'RNA_ELEMENTO_DI_AIUTO', 'Percentage', 'Status Economico']].rename(
            columns={'RNA_DENOMINAZIONE_BENEFICIARIO': 'Azienda', 'RNA_ELEMENTO_DI_AIUTO': 'Budget'}
        ))

    return df
