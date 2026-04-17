import streamlit as st
import pandas as pd
import io
import plotly.express as px

# Caricamenti
from settings import DEFAULT_KEYWORDS
from utils import  load_rna_data, is_target_row, render_database_misure, verifica_stato_clienti, colora_clienti

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Analisi strategica e qualificazione lead basata sui dati integrali RNA.")

# --- SIDEBAR ---
st.sidebar.header("1. Caricamento Dati")
uploaded_file = st.sidebar.file_uploader("Carica file RNA", type=["csv"])
uploaded_clienti = st.sidebar.file_uploader("Carica Database Clienti (Opzionale)", type=["csv"])

st.sidebar.header("2. Filtri Target")
default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area("Parole chiave target", value=default_kw)

btn_ricerca = st.sidebar.button("🔍 Aggiorna Analisi", use_container_width=True, type="primary")

# ANALISI
if uploaded_file is not None:
    try:
        
        # Loading dei dati
        df = load_rna_data(uploaded_file)

        # RICERCA TARGETS NEL DATAFRAME (e relativi importi)
        keywords_raw         = st.sidebar.text_area("Parole chiave target", value=DEFAULT_KEYWORDS)
        keywords             = [k.strip().upper() for k in keywords_raw.split(',')]
        df['IS_TARGET']      = df.apply(lambda row: is_target_row(row, keywords), axis=1)
        df['IMPORTO_TARGET'] = df.apply(lambda x: x['RNA_ELEMENTO_DI_AIUTO'] if x['IS_TARGET'] else 0, axis=1)
        
        # CHECK CLIENTI vs PROSPECT 
        if uploaded_clienti is not None:
            df = verifica_stato_clienti(df, uploaded_clienti)
        else:
            if 'STATO' not in df.columns:
                df['STATO'] = "⚪ PROSPECT"


        # RIEPILOGO

        # Metriche
        n_aziende             = df['RNA_CODICE_FISCALE_BENEFICIARIO'].nunique()
        n_aiuti_totali        = len(df)
        n_aiuti_target        = df['IS_TARGET'].sum()
        budget_totale         = df['RNA_ELEMENTO_DI_AIUTO'].sum()
        budget_target         = df['IMPORTO_TARGET'].sum()
        perc_aiuti_target     = (n_aiuti_target / n_aiuti_totali * 100) if n_aiuti_totali > 0 else 0
        perc_budget_target    = (budget_target / budget_totale * 100) if budget_totale > 0 else 0
        
        # Periodo temporale (YYYY-MM-DD)
        df['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df['RNA_DATA_CONCESSIONE'], errors='coerce')
        data_min = df['RNA_DATA_CONCESSIONE'].min().strftime('%d/%m/%Y') if not df['RNA_DATA_CONCESSIONE'].dropna().empty else "N/D"
        data_max = df['RNA_DATA_CONCESSIONE'].max().strftime('%d/%m/%Y') if not df['RNA_DATA_CONCESSIONE'].dropna().empty else "N/D"

        st.subheader("📌 Panoramica Analisi")
        #st.info(f"📅 **Periodo Analizzato:** dal {data_min} al {data_max}")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric("Periodo Analizzato", f"{data_max}", delta=f"dal {data_min}", delta_color="off")
            st.metric("Aziende", f"{n_aziende}")
            
        with m2:
            st.metric("Totale Aiuti", f"{n_aiuti_totali}")
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Budget Totale", f"€ {budget_totale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        with m3:
            st.metric("Aiuti Target", f"{n_aiuti_target}",delta=f"{perc_aiuti_target:.1f}% del totale")
            st.metric("Budget Target",
                      f"€ {budget_target:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                     delta=f"{perc_budget_target:.1f}% del budget totale")


        # Raggruppiamo per CF e Ragione Sociale per evitare duplicati
        # Se la colonna STATO è presente lo includiamo
        col_raggruppamento = ['RNA_CODICE_FISCALE_BENEFICIARIO', 'RAGIONE SOCIALE']
        if 'STATO' in df.columns:
            col_raggruppamento.append('STATO')

        report_aziende = df.groupby(col_raggruppamento).agg({
            'RNA_TITOLO_MISURA': 'count',       # Totale Aiuti
            'IS_TARGET': 'sum',                # Aiuti Target
            'RNA_ELEMENTO_DI_AIUTO': 'sum',     # Budget Totale
            'IMPORTO_TARGET': 'sum'            # Budget Target
        }).reset_index()

        # Rinominiamo le colonne per renderle leggibili nella tabella
        report_aziende = report_aziende.rename(columns={
            'RNA_CODICE_FISCALE_BENEFICIARIO': 'P.IVA',
            'RNA_TITOLO_MISURA': 'Aiuti',
            'IS_TARGET': 'Aiuti Target',
            'RNA_ELEMENTO_DI_AIUTO': 'Budget Totale (€)',
            'IMPORTO_TARGET': 'Budget Target (€)'
        })

        # Ordinamento per Budget Target decrescente (i lead più interessanti in alto)
        report_aziende = report_aziende.sort_values(by='Budget Target (€)', ascending=False)

        # --- UI: TABELLA ---
        st.subheader("📋 Analisi Dettagliata per Azienda")

        # Utilizziamo st.dataframe con configurazione delle colonne per formattare i numeri
        st.dataframe(
            report_aziende,
            column_config={
                "P.IVA": st.column_config.TextColumn("P.IVA"),
                "Ragione Sociale": st.column_config.TextColumn("Ragione Sociale", width="large"),
                "Aiuti": st.column_config.NumberColumn("Aiuti", format="%d"),
                "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d"),
                # Formattazione come importo valutario
                "Budget": st.column_config.NumberColumn(
                    "Budget (€)",
                    format="€ %.2f", # Mostra il simbolo € e 2 decimali
                ),
                "Budget Target": st.column_config.NumberColumn(
                    "Budget Target (€)",
                    format="€ %.2f", # Mostra il simbolo € e 2 decimali
                ),
            },
            use_container_width=True,
            hide_index=True
        )
        st.divider()

       
        # --- RICERCA AZIENDA E DETTAGLIO ---
        st.divider()
        st.subheader("🎯 Analisi Dettagliata per Azienda")
        search_txt = st.text_input("Inserisci Ragione Sociale per visualizzare i dettagli")

        if search_txt:
            azienda_details = df[df['RAGIONE SOCIALE'].str.contains(search_txt, case=False)].copy()
            
            if not azienda_details.empty:
                
                # 1. Definiamo l'ordine PRIORITARIO richiesto
                colonne_prioritarie = [
                    'RNA_DATA',                 # Data (mappata da RNA_DATA_CONCESSIONE)
                    'RNA_CAR',                  # CAR
                    'RNA_MISURA',               # Titolo Misura (mappata da RNA_TITOLO_MISURA)
                    'RNA_TITOLO_PROGETTO',      # Titolo Progetto
                    'RNA_IMPORTO',              # Elemento Aiuto (mappata da RNA_ELEMENTO_DI_AIUTO)
                    'is_target',                 # Spunta verde target
                    'RAGIONE SOCIALE',
                    'CF_TROVATO',
                ]
                
                # 2. Identifichiamo tutte le altre colonne che iniziano con RNA_ per non perderle
                altre_col_rna = [c for c in azienda_details.columns if c.startswith('RNA_') and c not in colonne_prioritarie]
                
                # 3. Costruiamo l'ordine finale: Priorità -> Altri dati RNA -> Eventuali altri campi
                ordine_finale = [c for c in colonne_prioritarie if c in azienda_details.columns] + altre_col_rna

                st.write(f"### Dettaglio estrazione: {azienda_details['RAGIONE SOCIALE'].iloc[0]}")
                
                # Visualizzazione Tabella
                st.dataframe(
                    azienda_details[ordine_finale].style.apply(
                        lambda r: ['background-color: #d4edda' if r['is_target'] else ''] * len(r), axis=1
                    ),
                    column_config={
                        "RNA_DATA": st.column_config.TextColumn("📅 Data"),
                        "RNA_CAR": st.column_config.TextColumn("CAR"),
                        "RNA_MISURA": st.column_config.TextColumn("📜 Titolo Misura", width="large"),
                        "RNA_TITOLO_PROGETTO": st.column_config.TextColumn("🏗️ Titolo Progetto", width="medium"),
                        "RNA_IMPORTO": st.column_config.NumberColumn("💰 Aiuto (€)", format="%.2f"),
                        "is_target": st.column_config.CheckboxColumn("🎯 Target"),
                        "RNA_LINK_TRASPARENZA_NAZIONALE": st.column_config.LinkColumn("🔗 Link Trasparenza"),
                        "RNA_LINK_TESTO_INTEGRALE_MISURA": st.column_config.LinkColumn("📄 Bando Originale"),
                    },
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning("Nessuna azienda trovata con questa ragione sociale.")

        # Download
        csv_buffer = io.BytesIO()
        report.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.sidebar.download_button("💾 Scarica Report (CSV)", csv_buffer.getvalue(), "Report_RNA.csv", "text/csv")

    except Exception as e:
        st.error(f"Errore: {e}")
else:
    st.info("👋 Carica il file per iniziare.")
