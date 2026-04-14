import streamlit as st
import pandas as pd
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")

# --- SIDEBAR ---
st.sidebar.header("1. Caricamento Dati")
uploaded_file = st.sidebar.file_uploader("Carica il file CSV arricchito", type=["csv"])

st.sidebar.header("2. Filtri Target")
default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area("Parole chiave (separate da virgola)", value=default_kw)

# TASTO DI RICERCA
btn_ricerca = st.sidebar.button("🔍 Aggiorna Analisi", use_container_width=True, type="primary")

st.sidebar.header("3. Ordinamento Report")
sort_options = {
    "Numero Aiuti Target": "N_AIUTI_TARGET",
    "Valore Aiuti Target (€)": "VALORE_TARGET_€",
    "Valore Totale (€)": "VALORE_TOTALE_€",
    "Numero Totale Aiuti": "N_TOT_AIUTI"
}
sort_choice = st.sidebar.selectbox("Ordina tabella per:", list(sort_options.keys()), index=0)

# --- LOGICA DI ELABORAZIONE ---
if uploaded_file is not None:
    try:
        @st.cache_data
        def load_data(file):
            return pd.read_csv(file, sep=';', encoding='utf-8-sig')

        df_raw = load_data(uploaded_file)
        df_raw['RNA_IMPORTO'] = pd.to_numeric(df_raw['RNA_IMPORTO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Elaborazione parole chiave
        keywords = [k.strip().upper() for k in keywords_raw.split(',')]
        
        def is_target_row(row_text):
            text = str(row_text).upper()
            return any(k in text for k in keywords)

        # Applichiamo il flag target a ogni riga del file originale
        df_raw['is_target'] = df_raw['RNA_MISURA'].apply(is_target_row)
        df_raw['importo_target'] = df_raw.apply(lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0, axis=1)

        # --- GENERAZIONE REPORT SINTETICO ---
        col_rna = ['RNA_PIVA', 'RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target', 'importo_target']
        col_ana = [c for c in df_raw.columns if c not in col_rna]
        
        report = df_raw.groupby('RAGIONE SOCIALE').agg({
            **{c: 'first' for c in col_ana if c != 'RAGIONE SOCIALE'},
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

        report = report.sort_values(by=sort_options[sort_choice], ascending=False)

        # --- KPI ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Aziende", len(report))
        k2.metric("Aiuti Totali", df_raw.shape[0])
        k3.metric("Volume Totale", f"€ {report['VALORE_TOTALE_€'].sum():,.0f}")
        k4.metric("Aiuti Target", int(report['N_AIUTI_TARGET'].sum()))

        st.divider()

        # --- RICERCA AZIENDA E DETTAGLIO EVIDENZIATO ---
        st.subheader("🎯 Dettaglio Azienda e Bandi Target")
        search_txt = st.text_input("Inserisci Ragione Sociale per vedere tutti i suoi bandi (Verde = Target)")

        if search_txt:
            # Filtriamo i bandi originali per quell'azienda
            azienda_details = df_raw[df_raw['RAGIONE SOCIALE'].str.contains(search_txt, case=False)].copy()
            
            if not azienda_details.empty:
                # Funzione per colorare le righe
                def highlight_target(row):
                    return ['background-color: #d4edda' if row.is_target else '' for _ in row]

                # Mostriamo solo le colonne interessanti per il dettaglio
                cols_to_show = ['RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target']
                st.dataframe(
                    azienda_details[cols_to_show].style.apply(highlight_target, axis=1),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Nessuna azienda trovata con questo nome.")

        st.divider()

        # --- TABELLA GENERALE ---
        st.subheader("📋 Report Generale")
        st.dataframe(
            report,
            column_config={
                "VALORE_TOTALE_€": st.column_config.NumberColumn(format="%.2f €"),
                "VALORE_TARGET_€": st.column_config.NumberColumn(format="%.2f €"),
            },
            hide_index=True,
            use_container_width=True
        )

        # Download
        csv_buffer = io.BytesIO()
        report.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.sidebar.download_button("💾 Scarica Report (CSV)", csv_buffer.getvalue(), "Analisi_RNA.csv", "text/csv")

    except Exception as e:
        st.error(f"Errore: {e}")
else:
    st.info("Carica il file CSV per iniziare.")
