import streamlit as st
import pandas as pd
import io
import plotly.express as px
from utils import render_database_misure, verifica_stato_clienti, colora_clienti

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Analisi strategica e qualificazione lead basata sui dati integrali RNA.")

# --- SIDEBAR ---
st.sidebar.header("1. Caricamento Dati")
uploaded_file = st.sidebar.file_uploader("Carica file RNA (Integrale)", type=["csv"])
uploaded_clienti = st.sidebar.file_uploader("Carica Database Clienti (Opzionale)", type=["csv"])

st.sidebar.header("2. Filtri Target")
default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area("Parole chiave target", value=default_kw)

btn_ricerca = st.sidebar.button("🔍 Aggiorna Analisi", use_container_width=True, type="primary")

st.sidebar.header("3. Ordinamento Report")
sort_options = {
    "Numero Aiuti Target": "N_AIUTI_TARGET",
    "Valore Aiuti Target (€)": "VALORE_TARGET_€",
    "Incidenza Volume (%)": "INCIDENZA_VOL_TARGET_%",
    "Valore Totale (€)": "VALORE_TOTALE_€"
}
sort_choice = st.sidebar.selectbox("Ordina tabella per:", list(sort_options.keys()), index=0)

# --- LOGICA DI ELABORAZIONE ---
if uploaded_file is not None:
    try:
        @st.cache_data
        def load_data(file):
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig', low_memory=False)
            mapping = {
                'RNA_TITOLO_MISURA': 'RNA_MISURA',
                'RNA_DATA_CONCESSIONE': 'RNA_DATA',
                'RNA_CODICE_FISCALE_BENEFICIARIO': 'RNA_PIVA',
                'RNA_ELEMENTO_DI_AIUTO': 'RNA_IMPORTO',
                'RNA_DES_STRUMENTO': 'RNA_STRUMENTO' # Mappato per la tabella dettaglio
            }
            df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
            return df

        df_raw = load_data(uploaded_file)

        if uploaded_clienti is not None:
            df_raw = verifica_stato_clienti(df_raw, uploaded_clienti)
        else:
            if 'STATO' not in df_raw.columns:
                df_raw['STATO'] = "⚪ PROSPECT"
        
        df_raw['RNA_IMPORTO'] = pd.to_numeric(df_raw['RNA_IMPORTO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        keywords = [k.strip().upper() for k in keywords_raw.split(',')]
        def is_target_row(row_text):
            text = str(row_text).upper()
            return any(k in text for k in keywords)

        df_raw['is_target'] = df_raw['RNA_MISURA'].astype(str).apply(is_target_row)
        df_raw['importo_target'] = df_raw.apply(lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0, axis=1)

        # --- GENERAZIONE REPORT ---
        col_escluse = ['RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'RNA_STRUMENTO', 'is_target', 'importo_target']
        col_ana = [c for c in df_raw.columns if c not in col_escluse and c != 'RAGIONE SOCIALE']
        
        report = df_raw.groupby('RAGIONE SOCIALE').agg({
            **{c: 'first' for c in col_ana},
            'RNA_MISURA': 'count',
            'RNA_IMPORTO': 'sum',
            'is_target': 'sum',
            'importo_target': 'sum'
        }).reset_index().rename(columns={
            'RNA_MISURA': 'N_TOT_AIUTI', 'RNA_IMPORTO': 'VALORE_TOTALE_€',
            'is_target': 'N_AIUTI_TARGET', 'importo_target': 'VALORE_TARGET_€'
        })

        report['INCIDENZA_VOL_TARGET_%'] = (report['VALORE_TARGET_€'] / report['VALORE_TOTALE_€'] * 100).fillna(0)
        report = report.sort_values(by=sort_options[sort_choice], ascending=False)

        st.divider()
        st.subheader("📋 Report Riepilogativo")
        st.dataframe(report.style.apply(colora_clienti, axis=1), use_container_width=True, hide_index=True)

        # --- DETTAGLIO AZIENDA (RIORDINATO SECONDO SCREENSHOT) ---
        # --- RICERCA AZIENDA E DETTAGLIO ---
        st.divider()
        st.subheader("🎯 Analisi Dettagliata per Azienda")
        search_txt = st.text_input("Inserisci Ragione Sociale per visualizzare i dettagli")

        if search_txt:
            azienda_details = df_raw[df_raw['RAGIONE SOCIALE'].str.contains(search_txt, case=False)].copy()
            
            if not azienda_details.empty:
                # 1. Definiamo l'ordine PRIORITARIO richiesto
                # Mappiamo i nomi reali del CSV arricchito
                colonne_prioritarie = [
                    'RNA_DATA',                 # Data (mappata da RNA_DATA_CONCESSIONE)
                    'RNA_CAR',                  # CAR
                    'RNA_MISURA',               # Titolo Misura (mappata da RNA_TITOLO_MISURA)
                    'RNA_TITOLO_PROGETTO',      # Titolo Progetto
                    'RNA_IMPORTO',              # Elemento Aiuto (mappata da RNA_ELEMENTO_DI_AIUTO)
                    'is_target'                 # Spunta verde target
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
                        "RNA_DATA": st.column_config.TextColumn("📅 Data Concessione"),
                        "RNA_CAR": st.column_config.TextColumn("CAR"),
                        "RNA_MISURA": st.column_config.TextColumn("📜 Titolo Misura", width="large"),
                        "RNA_TITOLO_PROGETTO": st.column_config.TextColumn("🏗️ Titolo Progetto", width="medium"),
                        "RNA_IMPORTO": st.column_config.NumberColumn("💰 Elemento Aiuto (€)", format="%.2f"),
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
