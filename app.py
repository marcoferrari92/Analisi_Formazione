import streamlit as st
import pandas as pd
import io
import plotly.express as px

# Importa le funzioni dal tuo file utils.py locale
from utils import render_database_misure, verifica_stato_clienti, colora_clienti

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Analisi strategica e qualificazione lead basata sui dati integrali RNA.")

# --- SIDEBAR ---
st.sidebar.header("1. Caricamento Dati")
# Carica il file "Elevo_Contatti_RNA_Excel_Integrale.csv"
uploaded_file = st.sidebar.file_uploader("Carica file RNA (Integrale)", type=["csv"])

uploaded_clienti = st.sidebar.file_uploader("Carica Database Clienti (Opzionale)", type=["csv"])

st.sidebar.header("2. Filtri Target")
default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area("Parole chiave target (separate da virgola)", value=default_kw)

# TASTO DI AGGIORNAMENTO
btn_ricerca = st.sidebar.button("🔍 Aggiorna Analisi", use_container_width=True, type="primary")

st.sidebar.header("3. Ordinamento Report")
sort_options = {
    "Numero Aiuti Target": "N_AIUTI_TARGET",
    "Valore Aiuti Target (€)": "VALORE_TARGET_€",
    "Incidenza Numero (%)": "INCIDENZA_N_TARGET_%",
    "Incidenza Volume (%)": "INCIDENZA_VOL_TARGET_%",
    "Valore Totale (€)": "VALORE_TOTALE_€",
    "Numero Totale Aiuti": "N_TOT_AIUTI"
}
sort_choice = st.sidebar.selectbox("Ordina tabella per:", list(sort_options.keys()), index=0)

# --- LOGICA DI ELABORAZIONE ---
if uploaded_file is not None:
    try:
        @st.cache_data
        def load_data(file):
            # Carica il file con delimitatore ; come rilevato nei metadati
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig', low_memory=False)
            
            # --- MAPPING COLONNE ---
            # Questo sistema traduce i nomi lunghi del file integrale nei nomi brevi usati dall'app
            mapping = {
                'RNA_TITOLO_MISURA': 'RNA_MISURA',
                'RNA_DATA_CONCESSIONE': 'RNA_DATA',
                'RNA_CODICE_FISCALE_BENEFICIARIO': 'RNA_PIVA',
                'RNA_ELEMENTO_DI_AIUTO': 'RNA_IMPORTO'
            }
            # Rinomina solo se le colonne esistono nel file
            df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
            return df

        df_raw = load_data(uploaded_file)

        # --- LOGICA DI CONFRONTO CLIENTI ---
        if uploaded_clienti is not None:
            df_raw = verifica_stato_clienti(df_raw, uploaded_clienti)
        else:
            if 'STATO' not in df_raw.columns:
                df_raw['STATO'] = "⚪ PROSPECT"
        
        # Pulizia Importi (gestisce virgole italiane e trasforma in numeri)
        df_raw['RNA_IMPORTO'] = pd.to_numeric(df_raw['RNA_IMPORTO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Elaborazione parole chiave
        keywords = [k.strip().upper() for k in keywords_raw.split(',')]
        
        def is_target_row(row_text):
            text = str(row_text).upper()
            return any(k in text for k in keywords)

        # Identificazione righe target
        if 'RNA_MISURA' in df_raw.columns:
            df_raw['is_target'] = df_raw['RNA_MISURA'].apply(is_target_row)
            df_raw['importo_target'] = df_raw.apply(lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0, axis=1)
        else:
            st.error("Colonna RNA_MISURA non trovata nel file.")
            st.stop()

        # --- GENERAZIONE REPORT SINTETICO ---
        # Identifichiamo le colonne "anagrafiche" (quelle che non iniziano con RNA_ e non sono di calcolo)
        col_escluse = ['RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target', 'importo_target', 'NOME_CLEAN', 'REGIONE_DERIVATA']
        col_ana = [c for c in df_raw.columns if c not in col_escluse and c != 'RAGIONE SOCIALE']
        
        report = df_raw.groupby('RAGIONE SOCIALE').agg({
            **{c: 'first' for c in col_ana},
            'RNA_MISURA': 'count',
            'RNA_IMPORTO': 'sum',
            'is_target': 'sum',
            'importo_target': 'sum'
        }).reset_index().rename(columns={
            'RNA_MISURA': 'N_TOT_AIUTI',
            'RNA_IMPORTO': 'VALORE_TOTALE_€',
            'is_target': 'N_AIUTI_TARGET',
            'importo_target': 'VALORE_TARGET_€'
        })

        # --- CALCOLO INCIDENZE ---
        report['INCIDENZA_N_TARGET_%'] = (report['N_AIUTI_TARGET'] / report['N_TOT_AIUTI'] * 100).fillna(0)
        report['INCIDENZA_VOL_TARGET_%'] = (report['VALORE_TARGET_€'] / report['VALORE_TOTALE_€'] * 100).fillna(0)

        # --- CALCOLO RANKING ---
        for col, rank_name in [('VALORE_TOTALE_€', 'RANK_VOL_TOT'), ('VALORE_TARGET_€', 'RANK_VOL_TARGET'),
                               ('N_TOT_AIUTI', 'RANK_N_TOT'), ('N_AIUTI_TARGET', 'RANK_N_TARGET'),
                               ('INCIDENZA_N_TARGET_%', 'RANK_INC_N'), ('INCIDENZA_VOL_TARGET_%', 'RANK_INC_VOL')]:
            report[rank_name] = report[col].rank(ascending=False, method='min').astype(int)

        # Ordinamento
        report = report.sort_values(by=sort_options[sort_choice], ascending=False)

        st.divider()
        render_database_misure(df_raw)
        
        st.divider()
        st.subheader("📋 Report Riepilogativo della Ricerca Target")
        
        # --- KPI GENERALI ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Aziende Totali", len(report))
        k2.metric("Volume Totale", f"€ {report['VALORE_TOTALE_€'].sum():,.0f}")
        k3.metric("Bandi Target", int(report['N_AIUTI_TARGET'].sum()))
        k4.metric("Volume Target", f"€ {report['VALORE_TARGET_€'].sum():,.0f}")
        
        # --- REPORT GENERALE ---
        st.dataframe(
            report.style.apply(colora_clienti, axis=1),
            column_config={
                "VALORE_TOTALE_€": st.column_config.NumberColumn("Budget Totale", format="%.2f €"),
                "VALORE_TARGET_€": st.column_config.NumberColumn("Budget Target", format="%.2f €"),
                "INCIDENZA_N_TARGET_%": st.column_config.NumberColumn("Incidenza N.", format="%.1f %%"),
                "INCIDENZA_VOL_TARGET_%": st.column_config.NumberColumn("Incidenza Vol.", format="%.1f %%"),
            },
            hide_index=True, 
            use_container_width=True
        )

        # --- BENCHMARK E LEAD ---
        with st.expander("📊 Analisi Benchmark di Mercato", expanded=True):
            imprese_attive = report[report['INCIDENZA_VOL_TARGET_%'] > 0]
            if not imprese_attive.empty:
                mediana_incidenza = imprese_attive['INCIDENZA_VOL_TARGET_%'].median()
                st.info(f"**Mediana Incidenza Volume:** {mediana_incidenza:.2f}%")
                
                fig = px.box(imprese_attive, x="INCIDENZA_VOL_TARGET_%", orientation='h', points="all", hover_name="RAGIONE SOCIALE")
                st.plotly_chart(fig, use_container_width=True)

                st.write("### 🚀 Lead Prioritari (Sotto Mediana)")
                df_target = report[(report['STATO'].str.contains("PROSPECT")) & (report['INCIDENZA_VOL_TARGET_%'] < mediana_incidenza)].copy()
                df_target['GAP_€'] = (df_target['VALORE_TOTALE_€'] * (mediana_incidenza / 100)) - df_target['VALORE_TARGET_€']
                st.dataframe(df_target[["RAGIONE SOCIALE", "VALORE_TOTALE_€", "INCIDENZA_VOL_TARGET_%", "GAP_€"]].sort_values('VALORE_TOTALE_€', ascending=False), use_container_width=True, hide_index=True)
            else:
                st.warning("Nessuna azienda attiva nel target trovata per il benchmark.")

        # --- RICERCA AZIENDA E DETTAGLIO INTEGRALE ---
        st.divider()
        st.subheader("🎯 Analisi Dettagliata per Azienda (Campi Integrali)")
        search_txt = st.text_input("Inserisci Ragione Sociale per visualizzare TUTTI i campi RNA")

        if search_txt:
            azienda_details = df_raw[df_raw['RAGIONE SOCIALE'].str.contains(search_txt, case=False)].copy()
            
            if not azienda_details.empty:
                # Mostriamo TUTTE le colonne che iniziano con "RNA_" più la ragione sociale
                cols_to_show = ['RAGIONE SOCIALE'] + [c for c in azienda_details.columns if c.startswith('RNA_')] + ['is_target']
                
                st.write(f"### Dettaglio estrazione per: {azienda_details['RAGIONE SOCIALE'].iloc[0]}")
                
                def highlight_target_rows(row):
                    return ['background-color: #d4edda' if row['is_target'] else ''] * len(row)

                st.dataframe(
                    azienda_details[cols_to_show].style.apply(highlight_target_rows, axis=1),
                    column_config={
                        "is_target": st.column_config.CheckboxColumn("Target?"),
                        "RNA_IMPORTO": st.column_config.NumberColumn(format="%.2f €"),
                        "RNA_LINK_TRASPARENZA_NAZIONALE": st.column_config.LinkColumn("Link Trasparenza"),
                        "RNA_LINK_TESTO_INTEGRALE_MISURA": st.column_config.LinkColumn("Link Bando")
                    },
                    use_container_width=True, hide_index=True
                )
            else:
                st.warning("Nessuna azienda trovata.")

        # --- DOWNLOAD REPORT ---
        csv_buffer = io.BytesIO()
        report.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.sidebar.download_button("💾 Scarica Report BI (CSV)", csv_buffer.getvalue(), "Report_Business_Intelligence.csv", "text/csv")

    except Exception as e:
        st.error(f"Errore critico nell'elaborazione: {e}")
else:
    st.info("👋 Carica il file 'Elevo_Contatti_RNA_Excel_Integrale.csv' per iniziare.")
