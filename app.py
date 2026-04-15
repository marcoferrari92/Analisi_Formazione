import streamlit as st
import pandas as pd
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Analisi strategica e qualificazione lead basata sui dati ufficiali RNA con integrazione Database Clienti.")

# --- SIDEBAR ---
st.sidebar.header("1. Caricamento Dati")
uploaded_file = st.sidebar.file_uploader("1. Carica il file CSV RNA (Semicolonne ';')", type=["csv"])
uploaded_clienti = st.sidebar.file_uploader("2. Carica Database Clienti (Opzionale - Virgole ',')", type=["csv"])

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
        def load_rna(file):
            return pd.read_csv(file, sep=';', encoding='utf-8-sig')

        df_raw = load_rna(uploaded_file)
        
        # --- GESTIONE CLIENTI (Incrocio P.IVA) ---
        lista_piva_clienti = []
        if uploaded_clienti:
            try:
                # Caricamento file clienti (basato sul formato CSV con virgola fornito)
                df_clienti = pd.read_csv(uploaded_clienti, sep=',', encoding='utf-8-sig')
                if 'Partita IVA' in df_clienti.columns:
                    # Pulizia P.IVA (rimozione spazi e conversione stringa)
                    df_clienti['Partita IVA'] = df_clienti['Partita IVA'].astype(str).str.strip().str.replace(' ', '')
                    lista_piva_clienti = df_clienti['Partita IVA'].unique().tolist()
                    st.sidebar.success(f"✅ {len(lista_piva_clienti)} Clienti identificati.")
                else:
                    st.sidebar.error("⚠️ Colonna 'Partita IVA' non trovata nel file clienti.")
            except Exception as e:
                st.sidebar.error(f"Errore caricamento clienti: {e}")

        # Pulizia Dati RNA
        df_raw['RNA_IMPORTO'] = pd.to_numeric(df_raw['RNA_IMPORTO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_raw['RNA_PIVA_CLEAN'] = df_raw['RNA_PIVA'].astype(str).str.strip().str.replace(' ', '')
        
        # Identificazione Stato (Cliente vs Prospect)
        df_raw['STATO'] = df_raw['RNA_PIVA_CLEAN'].apply(lambda x: "🟢 CLIENTE" if x in lista_piva_clienti else "⚪ PROSPECT")
        
        # Elaborazione parole chiave
        keywords = [k.strip().upper() for k in keywords_raw.split(',')]
        
        def is_target_row(row_text):
            text = str(row_text).upper()
            return any(k in text for k in keywords)

        # Identificazione righe target
        df_raw['is_target'] = df_raw['RNA_MISURA'].apply(is_target_row)
        df_raw['importo_target'] = df_raw.apply(lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0, axis=1)

        # --- GENERAZIONE REPORT SINTETICO ---
        col_rna = ['RNA_PIVA', 'RNA_PIVA_CLEAN', 'RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target', 'importo_target', 'STATO']
        col_ana = [c for c in df_raw.columns if c not in col_rna]
        
        report = df_raw.groupby('RAGIONE SOCIALE').agg({
            **{c: 'first' for c in col_ana if c != 'RAGIONE SOCIALE'},
            'RNA_MISURA': 'count',
            'RNA_IMPORTO': 'sum',
            'is_target': 'sum',
            'importo_target': 'sum',
            'STATO': 'first'  # Riporta se l'azienda è cliente o meno
        }).reset_index().rename(columns={
            'RNA_MISURA': 'N_TOT_AIUTI',
            'RNA_IMPORTO': 'VALORE_TOTALE_€',
            'is_target': 'N_AIUTI_TARGET',
            'importo_target': 'VALORE_TARGET_€'
        })

        # --- CALCOLO COLONNE INCIDENZA ---
        report['INCIDENZA_N_TARGET_%'] = (report['N_AIUTI_TARGET'] / report['N_TOT_AIUTI'] * 100).fillna(0)
        report['INCIDENZA_VOL_TARGET_%'] = (report['VALORE_TARGET_€'] / report['VALORE_TOTALE_€'] * 100).fillna(0)

        # --- RANKING ---
        report['RANK_VOL_TARGET'] = report['VALORE_TARGET_€'].rank(ascending=False, method='min').astype(int)
        report['RANK_N_TARGET'] = report['N_AIUTI_TARGET'].rank(ascending=False, method='min').astype(int)

        # Filtro per Stato (Prospect/Cliente)
        st.sidebar.divider()
        st.sidebar.subheader("Filtro Stato")
        filtro_stato = st.sidebar.multiselect("Mostra solo:", ["⚪ PROSPECT", "🟢 CLIENTE"], default=["⚪ PROSPECT", "🟢 CLIENTE"])
        report = report[report['STATO'].isin(filtro_stato)]

        # Ordinamento Finale
        report = report.sort_values(by=sort_options[sort_choice], ascending=False)

        # --- KPI GENERALI ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Aziende nel Report", len(report))
        k2.metric("Volume Totale (€)", f"€ {report['VALORE_TOTALE_€'].sum():,.0f}")
        k3.metric("Bandi Target", int(report['N_AIUTI_TARGET'].sum()))
        k4.metric("Volume Target (€)", f"€ {report['VALORE_TARGET_€'].sum():,.0f}")

        st.divider()

        # --- RICERCA AZIENDA E DETTAGLIO ---
        st.subheader("🎯 Analisi Dettagliata per Azienda")
        search_txt = st.text_input("Inserisci Ragione Sociale per visualizzare storia e ranking")

        if search_txt:
            azienda_details = df_raw[df_raw['RAGIONE SOCIALE'].str.contains(search_txt, case=False)].copy()
            if not azienda_details.empty:
                nome_esatto = azienda_details['RAGIONE SOCIALE'].iloc[0]
                info_rank = report[report['RAGIONE SOCIALE'] == nome_esatto].iloc[0]

                st.info(f"### {info_rank['STATO']} | {nome_esatto}")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Volume Target", f"{info_rank['VALORE_TARGET_€']:,.2f} €")
                    st.caption(f"Posizione in classifica: **{info_rank['RANK_VOL_TARGET']}**")
                with c2:
                    st.metric("Bandi Target", int(info_rank['N_AIUTI_TARGET']))
                    st.caption(f"Posizione in classifica: **{info_rank['RANK_N_TARGET']}**")
                with c3:
                    st.metric("Incidenza Target (Valore)", f"{info_rank['INCIDENZA_VOL_TARGET_%']:.1f}%")

                st.write("---")
                def highlight_target(row):
                    return ['background-color: #d4edda' if row['is_target'] else ''] * len(row)

                st.dataframe(
                    azienda_details[['RNA_DATA', 'RNA_MISURA', 'RNA_IMPORTO', 'is_target']].style.apply(highlight_target, axis=1),
                    column_config={"is_target": "Bando Target?", "RNA_IMPORTO": st.column_config.NumberColumn(format="%.2f €")},
                    use_container_width=True, hide_index=True
                )

        st.divider()

        # --- REPORT GENERALE ---
        st.subheader("📋 Report Riepilogativo Generale")
        
        def color_rows(row):
            color = '#e3f2fd' if "CLIENTE" in row['STATO'] else ''
            return [f'background-color: {color}'] * len(row)

        st.dataframe(
            report.style.apply(color_rows, axis=1),
            column_config={
                "VALORE_TOTALE_€": st.column_config.NumberColumn(format="%.2f €"),
                "VALORE_TARGET_€": st.column_config.NumberColumn(format="%.2f €"),
                "INCIDENZA_N_TARGET_%": st.column_config.NumberColumn(format="%.1f %%"),
                "INCIDENZA_VOL_TARGET_%": st.column_config.NumberColumn(format="%.1f %%"),
            },
            hide_index=True, use_container_width=True
        )

        # --- SEZIONE DOWNLOAD ---
        csv_buffer = io.BytesIO()
        report.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.sidebar.divider()
        st.sidebar.download_button("💾 Scarica Report (CSV)", csv_buffer.getvalue(), "Analisi_RNA_Full.csv", "text/csv")

    except Exception as e:
        st.error(f"Errore durante l'elaborazione: {e}")
else:
    st.info("👋 Benvenuto! Carica il file RNA nella sidebar per iniziare l'analisi.")
