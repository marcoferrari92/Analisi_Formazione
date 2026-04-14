import streamlit as st
import pandas as pd
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("""
Carica il file arricchito generato dallo script Python per ottenere una sintesi commerciale delle aziende.
""")

# --- SIDEBAR: INPUT DATI ---
st.sidebar.header("1. Caricamento Dati")
uploaded_file = st.sidebar.file_opener = st.sidebar.file_uploader("Carica il file CSV arricchito", type=["csv"])

st.sidebar.header("2. Filtri Ricerca")
default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area("Parole chiave (separate da virgola)", value=default_kw)

# --- LOGICA PRINCIPALE ---
if uploaded_file is not None:
    try:
        # Caricamento dati
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
        
        # Pulizia Importi
        df['RNA_IMPORTO'] = pd.to_numeric(df['RNA_IMPORTO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Elaborazione parole chiave
        keywords = [k.strip().upper() for k in keywords_raw.split(',')]
        
        def check_keywords(testo):
            testo = str(testo).upper()
            return any(k in testo for k in keywords)

        # Calcolo indicatori
        df['is_target'] = df['RNA_MISURA'].apply(check_keywords)
        df['importo_target'] = df.apply(lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0, axis=1)

        # --- AGGREGAZIONE REPORT ---
        colonne_rna = ['RNA_PIVA', 'RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target', 'importo_target']
        colonne_anagrafiche = [c for c in df.columns if c not in colonne_rna]
        
        report = df.groupby('RAGIONE SOCIALE').agg({
            **{c: 'first' for c in colonne_anagrafiche if c != 'RAGIONE SOCIALE'},
            'RNA_MISURA': 'count',
            'RNA_IMPORTO': 'sum',
            'is_target': 'sum',
            'importo_target': 'sum'
        }).reset_index()

        # Rinominiamo per l'utente
        report.columns = [
            'RAGIONE SOCIALE' if c == 'RAGIONE SOCIALE' else c for c in report.columns
        ]
        report = report.rename(columns={
            'RNA_MISURA': 'N_TOT_AIUTI',
            'RNA_IMPORTO': 'VALORE_TOTALE_€',
            'is_target': 'N_AIUTI_TARGET',
            'importo_target': 'VALORE_TARGET_€'
        })

        # --- VISUALIZZAZIONE DASHBOARD ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Aziende Analizzate", len(report))
        m2.metric("Aiuti Totali Trovati", df.shape[0])
        m3.metric("Volume Totale €", f"{report['VALORE_TOTALE_€'].sum():,.2f} €")
        m4.metric("Aiuti Target (Keyword)", int(report['N_AIUTI_TARGET'].sum()))

        st.divider()

        # Tabella Interattiva
        st.subheader("🔍 Analisi Dettagliata per Azienda")
        
        # Filtro rapido in app
        search = st.text_input("Cerca azienda nella tabella...")
        if search:
            report = report[report['RAGIONE SOCIALE'].str.contains(search, case=False)]

        # Visualizzazione con stile
        st.dataframe(
            report.sort_values(by='VALORE_TOTALE_€', ascending=False),
            column_config={
                "VALORE_TOTALE_€": st.column_config.NumberColumn(format="%.2f €"),
                "VALORE_TARGET_€": st.column_config.NumberColumn(format="%.2f €"),
                "EMAIL GENERICA": st.column_config.LinkColumn()
            },
            hide_index=True,
            use_container_width=True
        )

        # --- DOWNLOAD ---
        st.divider()
        csv_buffer = io.BytesIO()
        report.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="💾 Scarica Report Sintetico (CSV)",
            data=csv_buffer.getvalue(),
            file_name="Report_Sintesi_RNA.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Errore nel processare il file: {e}")
else:
    st.info("In attesa del caricamento del file CSV...")
