import streamlit as st
import pandas as pd
import plotly.graph_objects as go

GUIDA = """
**Questo sezione utilizza l'*Analisi di Pareto* per determinare l'*oligarchia* del Settore Target.**

#### 📈 Curva di Pareto
L'Analisi di Pareto si basa sul principio dell'**80/20**: spesso una piccola frazione di aziende (il 20%) assorbe la maggior parte delle risorse economiche (l'80%). 

Un mercato con una curva di Pareto piatta indica un settore democratico e frammentato; una curva a gomito indica un settore blindato dai grandi player.

#### 🎩 Status Economico nel Settore Target
In questa sezione, mappiamo la **concentrazione del potere economico** nel Settore Target estendendo l'analisi di Pareto a più scaglioni:
* Zona **Rossa (fino al 20%):** poche aziende leader che muovono il 20% di tutto il budget; complesse da acquisire ma fondamentali.
* Zona **Arancio (fino al 50%):** aziende che completano la metà dell'intero budget del Settore Target.
* Zona **Gialla (fino al 80%):** aziende che completano l'80% del Mercato Target (regola di Pareto). 
* Zona **Verde (fino al 95%):** aziende che completano la quasi totalità del Settore Target.  
* Zona **Blu (oltre il 95%):** troviamo i *Disinteressati*: aziende non interessate a investire nel Settore Target o troppo piccole per essere determinanti in questo settore. 
    
**N.B.**
L'appartenenza delle aziende ai vari scaglioni è individuata dallo **"Status Economico"** nella tabella riassuntiva di tutto il database.

"""


def pareto_analysis(df, guida_pareto=""):

    with st.popover("💡 Strategia"):
        st.info(GUIDA)

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
        # 0-20%: ROSSO
        if r <= soglie_indici.get(20, 0): 
            if r <= soglie_indici.get(5, 0):
                return "01. Top 5%", "#e74c3c"
            elif r <= soglie_indici.get(10, 0):
                return "02. Top 10%", "#e74c3c"
            else:
                return "03. Top 20%", "#e74c3c"
        # 20-50%: ARANCIO
        elif r <= soglie_indici.get(50, 0): 
            return "04. Top 50%", "#e67e22"
        # 50-80%: GIALLO
        elif r <= soglie_indici.get(80, 0): 
            return "05. Top 80%", "#f1c40f"
        # 80-95%: VERDE
        elif r <= soglie_indici.get(95, 0): 
            return "06. Top 95%", "#2ecc71"
        # Oltre 95%: BLU
        else: 
            return "07. Oltre 95%", "#3498db"

    # Applichiamo lo status e il colore
    res_class = df_pareto['N_Aziende_Count'].apply(classify_by_rank)
    df_pareto['Status Economico'] = [x[0] for x in res_class]
    df_pareto['color_marker'] = [x[1] for x in res_class]
    
    
    # --- 3. AGGIORNAMENTO GRAFICO ---
    fig_pareto = go.Figure()
    
    # Aggiungi la LINEA DI EQUITÀ (Diagonal)
    x_equita = [0, total_aziende]
    y_equita = [0, 100]
    fig_pareto.add_trace(go.Scatter(
        x=x_equita,
        y=y_equita,
        name="Equità Perfetta",
        line=dict(color='black', width=4, dash='dot'),
        yaxis="y2"
    ))

    # Barre (Scala Logaritmica)
    fig_pareto.add_trace(go.Bar(
        x=df_pareto['N_Aziende_Count'],
        y=df_pareto['RNA_ELEMENTO_DI_AIUTO'],
        marker=dict(
            color=df_pareto['color_marker'],
            line=dict(width=0.1)  
        ),
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
        bargap=0,
        yaxis=dict(title="Budget Target (€)", type="log", dtick=1, exponentformat="SI"),
        yaxis2=dict(title="% Cumulata", overlaying="y", side="right", range=[0, 105], ticksuffix="%"),
        template="plotly_white", height=600, 
        showlegend=True,
        legend=dict(
            orientation="h",      # Legenda orizzontale
            yanchor="top",        # Ancora la parte superiore della legenda...
            y=-0.2,               # ...sotto l'asse X (valore negativo)
            xanchor="center",     # Centra la legenda...
            x=0.5                 # ...a metà della larghezza del grafico
        )
    )
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    # --- 4. TABELLA RIEPILOGO CON RIGHE COLORATE ---
    df_report = pd.DataFrame(report_data)
    df_report['Status Economico'] = df_report['Status Economico'].apply(lambda x: x[0] if isinstance(x, tuple) else x)

    st.write("")
    st.dataframe(
        df_report,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget Cumulativo": st.column_config.NumberColumn(format="€ %,.0f"),
            "Status Economico": st.column_config.TextColumn("Ranking Scaglione")
        }
    )
    st.write("")

    # Arricchimento del dataframe originale per il return
    status_map = dict(zip(df_pareto['RNA_DENOMINAZIONE_BENEFICIARIO'], df_pareto['Status Economico']))
    df['Status Economico'] = df['RNA_DENOMINAZIONE_BENEFICIARIO'].map(status_map).fillna("Non Target")
    
    return df, color_map_status

    
