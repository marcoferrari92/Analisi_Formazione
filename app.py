import streamlit as st
import pandas as pd
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Carica il file arricchito per analizzare i finanziamenti e qualificare i tuoi lead.")

# --- SIDEBAR: INPUT E CONTROLLI ---
st.sidebar.header("1. Caricamento Dati")
uploaded_file = st.sidebar.file_uploader("Carica il file CSV arricchito", type=["csv"])

st.sidebar.header("2. Filtri Target")
default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area("Parole chiave (separate da virgola)", value=default_kw)

# TASTO DI RICERCA / AGGIORNAMENTO
btn_ricerca = st.sidebar.button("🔍 Avvia Ricerca / Aggiorna", use_container_width=True, type="primary")

st.sidebar.header("3. Ordinamento")
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
        # Caricamento e caching per velocità
        @st.cache_data
        def load_data(file):
            return pd.read_csv(file, sep=';', encoding='utf-8-sig')

        df_raw = load_data(uploaded_file)
        
        # Pulizia Importi
        df_raw['RNA_IMPORTO'] = pd.to_numeric(df_raw['RNA_IMPORTO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Eseguiamo i calcoli solo se il tasto viene premuto o se è la prima esecuzione
        # Streamlit gestisce lo stato, quindi usiamo btn_ricerca come trigger
        
        with st.spinner('Rielaborazione dati in corso...'):
            # Elaborazione parole chiave
            keywords = [k.strip().upper() for k in keywords_raw.split(',')]
            
            def check_keywords(testo):
                testo = str(testo).upper()
                return any(k in testo for k in keywords)

            # Calcolo indicatori target
            df_raw['is_target'] = df_raw['RNA_MISURA'].apply(check_keywords)
            df_raw['importo_target'] = df_raw.apply(lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0, axis=1)

            # --- AGGREGAZIONE ---
            col_rna = ['RNA_PIVA', 'RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target', 'importo_target']
            col_ana = [c for c in df_raw.columns if c not in col_rna]
            
            report = df_raw.groupby('RAGIONE SOCIALE').agg({
                **{c: 'first' for c in col_ana if c != 'RAGIONE SOCIALE'},
                'RNA_MISURA': 'count',
                'RNA_IMPORTO': 'sum',
                'is_target': 'sum',
                'importo_target': 'sum'
            }).reset_index()

            report = report.rename(columns={
                'RNA_MISURA': 'N_TOT_AIUTI',
                'RNA_IMPORTO': 'VALORE_TOTALE_€',
                'is_target': 'N_AIUTI_TARGET',
                'importo_target': 'VALORE_TARGET_€'
            })

            # Ordinamento
            report = report.sort_values(by=sort_options[sort_choice], ascending=False)

        # --- VISUALIZZAZIONE ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Aziende", len(report))
        k2.metric("Aiuti Totali", df_raw.shape[0])
        k3.metric("Volume Totale", f"€ {report['VALORE_TOTALE_€'].sum():,.0f}")
        k4.metric("Aiuti Target", int(report['N_AIUTI_TARGET'].sum()), delta_color="normal")

        st.divider()

        # Ricerca testuale veloce sulla tabella risultante
        search_txt = st.text_input("🎯 Cerca azienda specifica nel report...")
        if search_txt:
            report_disp = report[report['RAGIONE SOCIALE'].str.contains(search_txt, case=False)]
        else:
            report_disp = report

        st.dataframe(
            report_disp,
            column_config={
                "VALORE_TOTALE_€": st.column_config.NumberColumn(format="%.2f €"),
                "VALORE_TARGET_€": st.column_config.NumberColumn(format="%.2f €"),
                "EMAIL GENERICA": st.column_config.LinkColumn()
            },
            hide_index=True,
            use_container_width=True
        )

        # Download button
        csv_buffer = io.BytesIO()
        report.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.sidebar.download_button(
            label="💾 Scarica Report (CSV)",
            data=csv_buffer.getvalue(),
            file_name="Analisi_RNA_Target.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Si è verificato un errore: {e}")
else:
    st.info("👋 Benvenuto! Carica il file CSV generato dalla scansione dell'SSD per iniziare l'analisi.")
