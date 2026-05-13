import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import numpy as np


# Caricamenti
from settings import DEFAULT_KEYWORDS, GUIDA_BENCHMARK, STRATEGIA_BENCHMARK, GUIDA_PARETO, GUIDA_RICERCA, GUIDA_OUTLIER, STRATEGIA_OUTLIER
from utils import load_rna_data, is_target_row, format_it, format_pct, verifica_stato_clienti, colora_clienti, genera_output_confronto_csv, genera_output_confronto_pdf, crea_radar_azienda
from plots import create_centered_pie
from analisi_geo import geo_analysis
from analisi_time import time_analysis
from analisi_pareto import pareto_analysis
from analysis_benchmark import grafici_posizionamento

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Analisi strategica e qualificazione lead basata sui dati integrali RNA.")

# --- SIDEBAR ---
st.sidebar.header("1. Caricamento Dati")
# File RNA
uploaded_file = st.sidebar.file_uploader("Carica file RNA", type=["csv"])
# Database Clienti
uploaded_clienti = st.sidebar.file_uploader(
    "Carica database di confronto (opzionale)", 
    type=["csv", "pdf"]
)

st.sidebar.header("2. Filtri Target")
keywords_raw = st.sidebar.text_area("Parole chiave target", value=DEFAULT_KEYWORDS)
with st.sidebar.popover("ℹ️ Info logica di ricerca"):
    st.markdown(GUIDA_RICERCA)

st.sidebar.header("3. Range Temporale")
data_range = None



# ANALISI
if uploaded_file is not None:
    try:

        # Caricamento dei dati integrale
        df_raw = load_rna_data(uploaded_file)

        # --- FILTRO TEMPORALE  ---
        
        # Convertiamo la colonna data in datetime per poter calcolare i limiti
        df_raw['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_raw['RNA_DATA_CONCESSIONE'], errors='coerce')
        min_date_file = df_raw['RNA_DATA_CONCESSIONE'].min().date() if not df_raw['RNA_DATA_CONCESSIONE'].dropna().empty else None
        max_date_file = df_raw['RNA_DATA_CONCESSIONE'].max().date() if not df_raw['RNA_DATA_CONCESSIONE'].dropna().empty else None

        if min_date_file and max_date_file:
            data_range = st.sidebar.date_input(
                "Seleziona periodo di analisi",
                value=(min_date_file, max_date_file),
                min_value=min_date_file,
                max_value=max_date_file
            )
            
            # Applichiamo il filtro se l'utente ha selezionato un range completo (inizio e fine)
            if len(data_range) == 2:
                start_date, end_date = data_range
                df = df_raw[
                    (df_raw['RNA_DATA_CONCESSIONE'].dt.date >= start_date) & 
                    (df_raw['RNA_DATA_CONCESSIONE'].dt.date <= end_date)
                ].copy()
            else:
                df = df_raw.copy()
        else:
            df = df_raw.copy()
            st.sidebar.warning("⚠️ Nessuna data valida trovata nel file.")

        btn_ricerca = st.sidebar.button("🔍 Aggiorna Analisi", use_container_width=True, type="primary")

        # Generiamo il file di confronto basandoci sul df filtrato per periodo
        if uploaded_clienti is not None:
            if uploaded_clienti.name.lower().endswith('.pdf'):
                tuo_file_esito = genera_output_confronto_pdf(df, uploaded_clienti)
            else:
                tuo_file_esito = genera_output_confronto_csv(df, uploaded_clienti)
            
            if tuo_file_esito is not None:
                st.sidebar.divider()
                st.sidebar.subheader("🚩 Database Confronto")
                
                # Download del file arricchito
                csv_buffer = tuo_file_esito.to_csv(index=False, sep=';', encoding='utf-8-sig')
                
                st.sidebar.download_button(
                    label="📥 Scarica Esito Verifica (CSV)",
                    data=csv_buffer,
                    file_name=f"Verifica_Periodica_{uploaded_clienti.name}.csv",
                    mime="text/csv",
                    help="Scarica il tuo file con l'indicazione di chi ha ricevuto aiuti NEL PERIODO SELEZIONATO."
                )
                

       
        
        # RICERCA TARGETS NEL DATAFRAME (e relativi importi)
        keywords             = [k.strip().upper() for k in keywords_raw.split(',')]
        df['IS_TARGET']      = df.apply(lambda row: is_target_row(row, keywords), axis=1)
        df['IMPORTO_TARGET'] = df.apply(lambda x: x['RNA_ELEMENTO_DI_AIUTO'] if x['IS_TARGET'] else 0, axis=1)
        
        # CHECK CLIENTI vs PROSPECT 
        if uploaded_clienti is not None:
            df = verifica_stato_clienti(df, uploaded_clienti)
        else:
            if 'STATO' not in df.columns:
                df['STATO'] = "Unknow"
                
        st.divider();
        
        # RIEPILOGO
        
        # Famiglie di aziende
        aziende_totali        = set(df['RNA_CODICE_FISCALE_BENEFICIARIO'].unique())
        aziende_target        = set(df[df['IS_TARGET'] == 1]['RNA_CODICE_FISCALE_BENEFICIARIO'].unique())
        
        n_aziende             = len(aziende_totali)
        n_aziende_target      = len(aziende_target)
        
        n_aiuti_totali        = len(df)
        n_aiuti_target        = df['IS_TARGET'].sum()
        
        budget_totale         = df['RNA_ELEMENTO_DI_AIUTO'].sum()
        budget_target         = df['IMPORTO_TARGET'].sum()
        
        perc_aiuti_target     = (n_aiuti_target / n_aiuti_totali * 100) if n_aiuti_totali > 0 else 0
        perc_budget_target    = (budget_target / budget_totale * 100) if budget_totale > 0 else 0


        # PANORAMICA SETTORE TARGET ******************************
        
        # Periodo temporale (YYYY-MM-DD)
        df['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df['RNA_DATA_CONCESSIONE'], errors='coerce')
        data_min = df['RNA_DATA_CONCESSIONE'].min().strftime('%d/%m/%Y') if not df['RNA_DATA_CONCESSIONE'].dropna().empty else "N/D"
        data_max = df['RNA_DATA_CONCESSIONE'].max().strftime('%d/%m/%Y') if not df['RNA_DATA_CONCESSIONE'].dropna().empty else "N/D"

        st.subheader("🎯 Panoramica Settore Target")
        st.info(f"📅 **Periodo Analizzato:** dal {data_min} al {data_max}")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Aziende Attive", f"{n_aziende}")
            st.metric("Aziende Target", f"{n_aziende_target}", 
                      delta=f"{(n_aziende_target/n_aziende)*100:.1f}% del totale", delta_color = "normal")
        with m2:
            st.metric("Totale Aiuti", f"{n_aiuti_totali}")
            st.metric("Aiuti Target", f"{n_aiuti_target}",delta=f"{perc_aiuti_target:.1f}% del totale")
            
            
        with m3:
            # Budget Totale
            st.metric(label="Budget Totale", value=f"€ {budget_totale:,.0f}")
            
            # Budget Target
            st.metric(label="Budget Target",value=f"€ {budget_target:,.0f}",delta=f"{perc_budget_target:.1f}% del budget totale")

        # GRAFICI A TORTA 
        with m1:
            st.write("")
            st.plotly_chart(create_centered_pie([n_aziende_target, n_aziende - n_aziende_target]), 
                    use_container_width=True, 
                    config={'displayModeBar': False})
            st.caption("**Aziende Target**: Aziende attive nel settore target (budget target > 0€)")

        with m2:
            st.write("")
            st.plotly_chart(create_centered_pie([n_aiuti_target, n_aiuti_totali - n_aiuti_target]), 
                    use_container_width=True, 
                    config={'displayModeBar': False})

        with m3:
            st.write("")
            st.plotly_chart(create_centered_pie([budget_target, budget_totale - budget_target]), 
                    use_container_width=True, 
                    config={'displayModeBar': False})


        # --- FUNNEL CHART (QUALIFICAZIONE) ---
        st.write("")
        st.write("")
        with st.expander("👁️ Pentrazione Settore Target"):
            
            # 1. Recupero dei valori per i passaggi del funnel
            val_totali = n_aziende
            val_target = n_aziende_target
            
            # Calcolo aziende clienti nel target (se il database clienti è caricato)
            if 'STATO' in df.columns:
                # Contiamo i CF univoci che sono sia in target che già clienti
                val_clienti = df[(df['IS_TARGET'] == 1) & (df['STATO'].str.contains('MATCH', case=False, na=False))]['RNA_CODICE_FISCALE_BENEFICIARIO'].nunique()
            else:
                val_clienti = 0

            # Creazione del DataFrame per il grafico
            funnel_df = pd.DataFrame({
                "Fase": ["Aziende Totali", "Aziende Target", "Aziende Clienti"],
                "Numero": [val_totali, val_target, val_clienti]
            })

            # Generazione del Grafico
            fig_funnel = px.funnel(
                funnel_df, 
                x='Numero', 
                y='Fase',
                title="Penetrazione Settore Target",
                color_discrete_sequence=["#3498db"]
            )
            
            fig_funnel.update_traces(textinfo="value+percent initial")
            fig_funnel.update_layout(height=450, margin=dict(t=50, b=0, l=10, r=10))
            
            st.plotly_chart(fig_funnel, use_container_width=True, key="funnel_qualificazione_leads")
            
            
 
        # --- ANALISI GEOGRAFICA ---
        st.write("")
        st.write("")
        with st.expander("🗺️ Distribuzione Geografica Settore Target"):
            st.write("")
            geo_analysis(df)
        st.write("")
        st.write("")

        
        # --- SEZIONE TEMPORALE ---
        with st.expander("📅 Distribuzione Temporale Settore Target"):
            st.write("")
            time_analysis(df)
        st.write("")
        st.write("")

        
        # --- ANALISI RANKING E PARETO ---
        with st.expander("🏆 Ranking Beneficiari e Analisi di Mercato (Pareto)"):
            st.write("")
            df = pareto_analysis(df, guida_pareto=GUIDA_PARETO)
        st.write("")
        st.write("")



        
        
    
        # --- 1. PREPARAZIONE COLONNE RAGGRUPPAMENTO ---
        # Usiamo questa lista dinamica per evitare il crash se c'è o meno lo STATO
        col_raggruppamento = ['RNA_CODICE_FISCALE_BENEFICIARIO', 'RAGIONE SOCIALE', 'RNA_REGIONE_BENEFICIARIO']
        if 'STATO' in df.columns:
            col_raggruppamento.append('STATO')

        # --- 2. RAGGRUPPAMENTO (Usando la variabile dinamica) ---
        report_aziende = df.groupby(col_raggruppamento).agg({
            'RNA_TITOLO_MISURA': 'count',
            'IS_TARGET': 'sum',
            'RNA_ELEMENTO_DI_AIUTO': 'sum',
            'IMPORTO_TARGET': 'sum'
        }).reset_index()

        # --- 3. CALCOLO Fo e Fe  ---
        report_aziende['Fo'] = (report_aziende['IS_TARGET'] / report_aziende['RNA_TITOLO_MISURA'] * 100).fillna(0)
        report_aziende['Fe'] = (report_aziende['IMPORTO_TARGET'] / report_aziende['RNA_ELEMENTO_DI_AIUTO'] * 100).fillna(0)

        # --- 4. RINOMINA ---
        # Usiamo rename invece di .columns = [...]
        mappa_nomi = {
            'RNA_CODICE_FISCALE_BENEFICIARIO': 'P.IVA',
            'RAGIONE SOCIALE': 'Ragione Sociale',
            'RNA_TITOLO_MISURA': 'Aiuti',
            'RNA_REGIONE_BENEFICIARIO': 'Regione',
            'IS_TARGET': 'Aiuti Target',
            'RNA_ELEMENTO_DI_AIUTO': 'Budget',
            'IMPORTO_TARGET': 'Budget Target'
        }
        report_aziende = report_aziende.rename(columns=mappa_nomi)

        # --- 1. CALCOLO BENCHMARK (Solo su aziende con attività Target) ---
        df_benchmark_1 = report_aziende[report_aziende['Budget Target'] > 0]
        df_benchmark_2 = report_aziende[report_aziende['Budget'] > 0]
        
        if not df_benchmark_1.empty:
            med_aiuti              = df_benchmark_2['Aiuti'].median()
            med_budget             = df_benchmark_2['Budget'].median()
            med_aiuti_target       = float(df_benchmark_1['Aiuti Target'].median())
            med_budget_target      = float(df_benchmark_1['Budget Target'].median())
            med_Fo                 = float(df_benchmark_1['Fo'].median())
            med_Fe                 = float(df_benchmark_1['Fe'].median())
        else:
            # Valori di fallback per evitare divisioni per zero se il file è vuoto
            med_aiuti_target, med_budget_target, med_Fo, med_Fe = 1.0, 1.0, 1.0, 1.0

        # Ordiniamo le colonne per assicurarci che la Regione sia dopo Ragione Sociale
        ordine_colonne = ['P.IVA', 'Ragione Sociale', 'Regione'] + [c for c in report_aziende.columns if c not in ['P.IVA', 'Ragione Sociale', 'Regione']]
        report_aziende = report_aziende[ordine_colonne]

        # --- 5. TABELLA ---
        st.write("")
        st.dataframe(
            report_aziende.style.apply(colora_clienti, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "P.IVA": st.column_config.TextColumn("P.IVA"),
                "Ragione Sociale": st.column_config.TextColumn("Ragione Sociale", width="large"),
                "Aiuti": st.column_config.NumberColumn("Aiuti", format="%d"),
                "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d"),
                "Budget": st.column_config.NumberColumn(
                    "Budget Totale (€)",
                    format="€ %,.2f"),
                "Budget Target": st.column_config.NumberColumn(
                    "Budget Target (€)",
                    format="€ %,.2f"),
                "Fo": st.column_config.NumberColumn(
                    "Fo (%)",
                    format="%.1f%%",
                    help="Incidenza numero aiuti target"),
                "Fe": st.column_config.NumberColumn(
                    "Fe (%)",
                    format="%.1f%%",
                    help="Incidenza budget target")
            }
        )
        st.write("")

        
        # --- 2. UI: RIQUADRO BENCHMARK ---
        st.subheader("📈 Benchmark Settore Target")
        
        with st.popover("📖 Metodologia"):
            st.markdown(GUIDA_BENCHMARK)
            
        # Creiamo un contenitore con bordo (stile card)
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write("**Numero Aiuti per Azienda**")
                st.metric("Mediana Totale", f"{med_aiuti:.1f}")
                st.metric("Mediana Target", f"{med_aiuti_target:.1f}",
                          delta=f"{(med_aiuti_target/med_aiuti)*100:.1f}% del totale", delta_color="normal")
                
                # LOGICA INVERTITA: Aziende SOPRA la mediana
                sopra_med_aiuti_target = len(df_benchmark_1[df_benchmark_1['Aiuti Target'] > med_aiuti_target])
                st.caption(f"🚀 {sopra_med_aiuti_target} aziende sopra mediana delle {n_aziende_target} attive nel settore target")
        
            with col2:
                st.write("**Budget per Azienda**")
                st.metric(label="Mediana Totale", value=f"€ {med_budget:,.0f}")
                st.metric(
                    label="Mediana Target", 
                    value=f"€ {med_budget_target:,.0f}",
                    delta=f"{(med_budget_target/med_budget)*100:.1f}% del totale", 
                    delta_color="normal"
                )
                
                # LOGICA INVERTITA: Aziende SOPRA la mediana
                sopra_med_budget_target = len(df_benchmark_1[df_benchmark_1['Budget Target'] > med_budget_target])
                st.caption(f"🚀 {sopra_med_budget_target} aziende sopra mediana delle {n_aziende_target} attive nel settore target")
        
            with col3:
                st.write("**Fattore Fo**")
                st.metric("Mediana", f"{med_Fo:.1f}%")
                
                # LOGICA INVERTITA: Aziende SOPRA la mediana
                sopra_med_Fo = len(df_benchmark_1[df_benchmark_1['Fo'] > med_Fo])
                st.caption(f"🚀 {sopra_med_Fo} aziende sopra mediana")
                
            with col4:
                st.write("**Fattore Fe**")
                st.metric("Mediana", f"{med_Fe:.1f}%")
                
                # LOGICA INVERTITA: Aziende SOPRA la mediana
                sopra_med_Fe = len(df_benchmark_1[df_benchmark_1['Fe'] > med_Fe])
                st.caption(f"🚀 {sopra_med_Fe} aziende sopra mediana")
                    

        # --- GRAFICI POSIZIONAMENTI ---
        
        # Definiamo le colonne da mappare e il template
        custom_data = ['Aiuti', 'Aiuti Target', 'Fo', 'Budget', 'Budget Target', 'Fe']
        
        custom_template = (
            "<b>%{hovertext}</b><br>" +
            "------------------<br>" +
            "Aiuti: %{customdata[0]}<br>" +
            "Aiuti Target: %{customdata[1]}<br>" +
            "Fattore Fo: %{customdata[2]:.1f}%<br>" +
            "Budget Totale: €%{customdata[3]:,.0f}<br>" +
            "Budget Target: €%{customdata[4]:,.0f}<br>" +
            "Fattore Fe: %{customdata[5]:.1f}%<br>" +
            "<extra></extra>"
        )
        
        # Filtriamo: Budget Target deve essere > 1 per eliminare centesimi o errori di sistema
        df_plot = report_aziende[report_aziende['Budget Target'] > 1].copy()
        
        if not df_plot.empty:
            st.write("")   
            
            grafici_posizionamento(df_plot, med_Fo, med_Fe, custom_data, custom_template)   
            

            with st.expander("📈 Analisi Outliers"):

                st.subheader("🔝 Analisi Outliers")
                col_info1, col_info2, col_spacer = st.columns([0.2, 0.2, 0.6]) 
                with col_info1:
                    with st.popover("📖 Guida ai grafici"):
                        st.markdown(GUIDA_OUTLIER)
                with col_info2:   
                    with st.popover("💡 Strategia"):
                        st.info(STRATEGIA_OUTLIER)
                    
                
                
                # Funzione helper per creare i grafici con lo stesso stile
                def crea_box_orizzontale(df, col, titolo, colore):
                    
                    # 2. Creiamo il boxplot base
                    fig = px.box(
                        df, 
                        x=col, 
                        points="all", 
                        hover_name="Ragione Sociale",
                        title=titolo,
                        color_discrete_sequence=[colore],
                        custom_data=custom_data  
                    )
                    
                    # 3. Personalizziamo i punti e il tooltip
                    fig.update_traces(
                        pointpos=0, 
                        jitter=0.7, 
                        marker=dict(opacity=0.6, size=7), 
                        hovertemplate=custom_template
                    )
                    
                    fig.update_layout(
                        height=280, 
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis_title=""
                    )
                    return fig
                    
                # GRAFICO: NUMERO AIUTI TARGET
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Aiuti Target", "Distribuzione Numero Aiuti Target", "#9b59b6"),
                    use_container_width=True
                )
                # GRAFICO: Fo
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Fo", "Distribuzione Fattore Fo", "#3498db"),
                    use_container_width=True
                )
                # GRAFICO: BUDGET TARGET
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Budget Target", "Distribuzione Budget Target (€)", "#2ecc71"),
                    use_container_width=True
                )
                # GRAFICO: Fe
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Fe", "Distribuzione Fattore Fe", "#e67e22"),
                    use_container_width=True
                )
                
        else:
            st.info("Nessun dato target disponibile per i grafici.")
    
        st.divider()

       
        # --- RICERCA AZIENDA E DETTAGLIO ---
        st.divider()
        st.subheader("🎯 Analisi Dettagliata per Azienda")
        search_txt = st.text_input("Inserisci Ragione Sociale per visualizzare i dettagli")
        st.write("")
        
        if search_txt:
            # 1. Filtriamo le statistiche aggregate
            scelte = report_aziende[report_aziende['Ragione Sociale'].str.contains(search_txt, case=False, na=False)]
            
            if not scelte.empty:
                # Se ci sono più aziende, ne facciamo scegliere una
                if len(scelte) > 1:
                    nome_scelto = st.selectbox("Seleziona l'azienda esatta:", scelte['Ragione Sociale'].tolist())
                    row = scelte[scelte['Ragione Sociale'] == nome_scelto].iloc[0]
                else:
                    row = scelte.iloc[0]
        
                # --- 2. RECUPERO DETTAGLI SINGOLI BANDI (Ecco azienda_details) ---
                # Filtriamo il DF originale per mostrare l'elenco dei progetti
                azienda_details = df[df['RAGIONE SOCIALE'] == row['Ragione Sociale']].copy()
        
                st.markdown(f"### 🔍 Analisi Strategica: {row['Ragione Sociale']}")
        
                # --- 3. VISUALIZZAZIONE METRICHE ---
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    st.metric("Aiuti Target", f"{row['Aiuti Target']:.0f}", delta=f"{row['Aiuti Target'] - med_aiuti_target:+.1f} vs med")
                with b2:
                    val_b = float(row['Budget Target'])
                    st.metric("Budget Target", f"€ {val_b:,.0f}".replace(',', '.'), delta=f"€ {val_b - med_budget_target:,.0f}".replace(',', '.'))
                with b3:
                    st.metric("Fattore Fo", f"{row['Fo']:.1f}%", delta=f"{row['Fo'] - med_Fo:+.1f}% vs med")
                with b4:
                    st.metric("Fattore Fe", f"{row['Fe']:.1f}%", delta=f"{row['Fe'] - med_Fe:+.1f}% vs med")
        
                # --- 4. RADAR CHART ---
                st.write("")
                fig_radar = crea_radar_azienda(row, med_Fo, med_Fe, med_aiuti_target, med_budget_target)
                st.plotly_chart(fig_radar, use_container_width=True)
            
                
            if not azienda_details.empty:
                # 1. Mapping di sicurezza (se i nomi nel DF sono diversi da quelli desiderati per la tabella)
                # Assicuriamoci che le colonne esistano prima di rinominare o usare
                map_colonne = {
                    'RNA_DATA_CONCESSIONE': 'RNA_DATA',
                    'RNA_TITOLO_MISURA': 'RNA_MISURA',
                    'RNA_ELEMENTO_DI_AIUTO': 'RNA_IMPORTO',
                    'IS_TARGET': 'is_target'
                }
        
                # Rinominiamo solo quelle presenti per evitare errori
                azienda_details = azienda_details.rename(columns={k: v for k, v in map_colonne.items() if k in azienda_details.columns})

                # 2. Definizione Ordine
                colonne_prioritarie = [
                    'RNA_DATA', 'RNA_CAR', 'RNA_MISURA', 'RNA_TITOLO_PROGETTO', 
                    'RNA_IMPORTO', 'is_target', 'RAGIONE SOCIALE', 'CF_TROVATO'
                ]
        
                # Filtriamo solo quelle che esistono davvero dopo il rinnovo
                ordine_esistente = [c for c in colonne_prioritarie if c in azienda_details.columns]
                altre_col_rna = [c for c in azienda_details.columns if c.startswith('RNA_') and c not in ordine_esistente]
                ordine_finale = ordine_esistente + altre_col_rna

                st.write(f"### Dettaglio estrazione: {azienda_details['RAGIONE SOCIALE'].iloc[0]}")
        
                # Visualizzazione Tabella con stile
                st.dataframe(
                    azienda_details[ordine_finale].style.apply(
                        lambda r: ['background-color: #d4edda' if r.get('is_target', 0) == 1 else ''] * len(r), axis=1
                    ),
                    column_config={
                        "RNA_DATA": st.column_config.DateColumn("📅 Data", format="DD/MM/YYYY"),
                        "RNA_CAR": st.column_config.TextColumn("CAR"),
                        "RNA_MISURA": st.column_config.TextColumn("📜 Titolo Misura", width="large"),
                        "RNA_TITOLO_PROGETTO": st.column_config.TextColumn("🏗️ Titolo Progetto", width="medium"),
                        "RNA_IMPORTO": st.column_config.NumberColumn("💰 Aiuto (€)", format="€ %.2f"),
                        "is_target": st.column_config.CheckboxColumn("🎯 Target"),
                        "RNA_LINK_TRASPARENZA_NAZIONALE": st.column_config.LinkColumn("🔗 Link Trasparenza"),
                        "RNA_LINK_TESTO_INTEGRALE_MISURA": st.column_config.LinkColumn("📄 Bando"),
                    },
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning(f"Nessuna azienda trovata per: {search_txt}")

        
        try:
            # Verifichiamo quale DataFrame usare per il download
            df_da_scaricare = report_aziende if 'report_aziende' in locals() else df
    
            csv_buffer = io.BytesIO()
            df_da_scaricare.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
            st.sidebar.download_button(
                label="💾 Scarica Report (CSV)",
                data=csv_buffer.getvalue(),
                file_name="Report_RNA.csv",
                mime="text/csv"
            )
        except NameError:
            st.sidebar.error("⚠️ Errore: DataFrame per il download non trovato.")

    except Exception as e:
        st.error(f"Errore generale nell'applicazione: {e}")

else:
    st.info("👋 Carica il file per iniziare.")
