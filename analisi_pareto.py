import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def pareto_analysis(df, guida_pareto=""):
    """
    Esegue l'analisi di Pareto con classificazione coerente tra riepilogo e dettaglio.
    """
    df_targ = df[df['IS_TARGET'] == 1].copy()
    
    if df_targ.empty:
        st.warning("Nessun dato disponibile per il settore target.")
        return df

    # --- 1. PREPARAZIONE DATI ---
    # Raggruppiamo per beneficiario e ordiniamo per budget decrescente
    df_pareto = df_targ.groupby('RNA_DENOMINAZIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_pareto = df_pareto.sort_values(by='RNA_ELEMENTO_DI_AIUTO', ascending=False)
    
    total_budget = df_pareto['RNA_ELEMENTO_DI_AIUTO'].sum()
    total_aziende = len(df_pareto)
    
    df_pareto['Cumsum'] = df_pareto['RNA_ELEMENTO_DI_AIUTO'].cumsum()
    df_pareto['Percentage'] = (df_pareto['Cumsum'] / total_budget) * 100
    # N_Aziende_Count è il nostro "Ranking" (1, 2, 3...)
    df_pareto['N_Aziende_Count'] = range(1, total_aziende + 1)

    # --- 2. CALCOLO SOGLIE E CLASSIFICAZIONE COERENTE ---
    
    # 2A. MAPPA COLORI SACGLIONI
    color_map_status = {
        "01. Top 5%": "#e74c3c",    # Rosso
        "02. Top 10%": "#f39c12",   # Arancio
        "03. Top 20%": "#f1c40f",   # Giallo
        "04. Top 50%": "#2ecc71",   # Verde chiaro
        "05. Top 80%": "#27ae60",   # Verde scuro
        "06. Top 95%": "#3498db",   # Blu chiaro
        "07. Oltre 95%": "#2980b9"  # Blu scuro
    }

    # 2B. SCAGLIONI
    scaglioni = [5, 10, 20, 50, 80, 95]
    soglie_indici = {}
    report_data = []

    # Identifichiamo il "punto di taglio" (l'indice dell'azienda) per ogni scaglione
    for s in scaglioni:
        subset = df_pareto[df_pareto['Percentage'] >= s]
        if not subset.empty:
            row = subset.iloc[0]
            idx_taglio = int(row['N_Aziende_Count'])
            soglie_indici[s] = idx_taglio
            
            report_data.append({
                "Status Economico": f"Fino a {s}%",
                "N. Aziende": idx_taglio,
                "% su Totale Aziende": f"{(idx_taglio / total_aziende * 100):.2f}%",
                "Budget Cumulativo": f"€ {row['Cumsum']:,.0f}"
            })

    # Funzione di classificazione basata sul RANK (N_Aziende_Count)
    # L'ordine elif garantisce che se una riga è <= soglia 5%, riceva "Top 5%" e si fermi.
    def classify_by_rank(r):
        if r <= soglie_indici.get(5, 0): 
            return "01. Top 5%", "#e74c3c"
        elif r <= soglie_indici.get(10, 0): 
            return "02. Top 10%", "#e74c3c"
        elif r <= soglie_indici.get(20, 0): 
            return "03. Top 20%", "#e74c3c"
        elif r <= soglie_indici.get(50, 0): 
            return "04. Top 50%", "#f1c40f"
        elif r <= soglie_indici.get(80, 0): 
            return "05. Top 80%", "#2ecc71"
        elif r <= soglie_indici.get(95, 0): 
            return "06. Top 95%", "#2ecc71"
        else: 
            return "07. Oltre 95%", "#3498db"

    # Applichiamo lo status e il colore
    res_class = df_pareto['N_Aziende_Count'].apply(classify_by_rank)
    df_pareto['Status Economico'] = [x[0] for x in res_class]
    df_pareto['color_marker'] = [x[1] for x in res_class]

    # --- 3. GRAFICO ---
    fig_pareto = go.Figure()

    # Barre (Scala Logaritmica)
    fig_pareto.add_trace(go.Bar(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['RNA_ELEMENTO_DI_AIUTO'],
        marker_color=df_pareto['color_marker'],
        name="Budget Azienda",
        customdata=df_pareto['Status Economico'],
        hovertemplate="<b>%{customdata}</b><br>Budget: %{y:,.2f}€<extra></extra>"
    ))

    # Curva di Pareto
    fig_pareto.add_trace(go.Scatter(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['Percentage'],
        name="% Cumulata",
        line=dict(color='#2c3e50', width=3),
        yaxis="y2"
    ))

    # Aggiunta linee di soglia nel grafico
    for s in scaglioni:
        if s in soglie_indici:
            fig_pareto.add_hline(y=s, yref="y2", line_dash="dash", line_color="red", opacity=0.2)
            fig_pareto.add_trace(go.Scatter(
                x=[soglie_indici[s]], y=[s], mode='markers+text',
                marker=dict(color='black', size=8, symbol='diamond'),
                text=[f"<b>{s}%</b>"], textposition="top left", yaxis="y2", showlegend=False
            ))

    fig_pareto.update_layout(
        title="Concentrazione Settore Target",
        xaxis_title="Numero Aziende",
        yaxis=dict(title="Budget Target (€)", type="log", dtick=1, exponentformat="SI"),
        yaxis2=dict(title="% Cumulata", overlaying="y", side="right", range=[0, 105], ticksuffix="%"),
        template="plotly_white", height=600
    )
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    # --- 4. TABELLA RIEPILOGO CON RIGHE COLORATE ---
    report_data = []
    for s in scaglioni:
        if s in soglie_indici:
            idx = soglie_indici[s]
            row_p = df_pareto[df_pareto['N_Aziende_Count'] == idx].iloc[0]
            report_data.append({
                "Status": classify_by_rank(idx), # SOLO IL TESTO
                "Soglia": f"{s}%",
                "N. Aziende": idx,
                "% Aziende": f"{(idx / len(df_pareto) * 100):.2f}%",
                "Budget Cumulativo": row_p['Cumsum']
            })

    df_report = pd.DataFrame(report_data)

    # FUNZIONE STILE: legge il testo e applica il colore
    def apply_row_style(row):
        color = color_map_status.get(row['Status'], "")
        text_color = "black" if any(x in row['Status'] for x in ["20%", "50%"]) else "white"
        return [f"background-color: {color}; color: {text_color}; font-weight: bold;"] * len(row)

    st.write("")
    st.write("")
    st.dataframe(
        df_report.style.apply(apply_row_style, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={"Budget Cumulativo": st.column_config.NumberColumn(format="€ %,.0f")}
    )

    # Arricchimento del dataframe originale per il return
    status_map = dict(zip(df_pareto['RNA_DENOMINAZIONE_BENEFICIARIO'], df_pareto['Status Economico']))
    df['Status Economico'] = df['RNA_DENOMINAZIONE_BENEFICIARIO'].map(status_map).fillna("Non Target")
    
    return df, color_map_status

    
