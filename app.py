import streamlit as st
import pandas as pd
import io
import plotly.express as px

# Caricamenti
from settings import DEFAULT_KEYWORDS
from utils import  load_rna_data, is_target_row, format_it, format_pct, render_database_misure, verifica_stato_clienti, colora_clienti

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
                df['STATO'] = "Unknow"


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


        # --- 1. PREPARAZIONE COLONNE RAGGRUPPAMENTO ---
        # Usiamo questa lista dinamica per evitare il crash se c'è o meno lo STATO
        col_raggruppamento = ['RNA_CODICE_FISCALE_BENEFICIARIO', 'RAGIONE SOCIALE']
        if 'STATO' in df.columns:
            col_raggruppamento.append('STATO')

        # --- 2. RAGGRUPPAMENTO (Usando la variabile dinamica) ---
        report_aziende = df.groupby(col_raggruppamento).agg({
            'RNA_TITOLO_MISURA': 'count',
            'IS_TARGET': 'sum',
            'RNA_ELEMENTO_DI_AIUTO': 'sum',
            'IMPORTO_TARGET': 'sum'
        }).reset_index()

        # --- 3. CALCOLO F1 e F2 (Prima di rinominare le colonne!) ---
        report_aziende['F1'] = (report_aziende['IS_TARGET'] / report_aziende['RNA_TITOLO_MISURA'] * 100).fillna(0)
        report_aziende['F2'] = (report_aziende['IMPORTO_TARGET'] / report_aziende['RNA_ELEMENTO_DI_AIUTO'] * 100).fillna(0)

        # --- 4. RINOMINA ROBUSTA (Evita il Length Mismatch) ---
        # Usiamo rename invece di .columns = [...]
        mappa_nomi = {
            'RNA_CODICE_FISCALE_BENEFICIARIO': 'P.IVA',
            'RAGIONE SOCIALE': 'Ragione Sociale',
            'RNA_TITOLO_MISURA': 'Aiuti',
            'IS_TARGET': 'Aiuti Target',
            'RNA_ELEMENTO_DI_AIUTO': 'Budget',
            'IMPORTO_TARGET': 'Budget Target'
        }
        report_aziende = report_aziende.rename(columns=mappa_nomi)

        # Ordiniamo prima di formattare (fondamentale!)
        report_aziende = report_aziende.sort_values(by='Budget Target', ascending=False)

        # --- 5. FORMATTAZIONE PER VISUALIZZAZIONE ---
        report_visual = report_aziende.copy()
        report_visual['Budget'] = report_visual['Budget'].apply(format_it)
        report_visual['Budget Target'] = report_visual['Budget Target'].apply(format_it)
        report_visual['F1'] = report_visual['F1'].apply(format_pct)
        report_visual['F2'] = report_visual['F2'].apply(format_pct)

        # --- 6. VISUALIZZAZIONE ---
        st.dataframe(
            report_visual.style.apply(colora_clienti, axis=1), 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ragione Sociale": st.column_config.TextColumn("Ragione Sociale", width="large"),
                "F1": st.column_config.TextColumn("F1 (%)", help="Incidenza numero aiuti target"),
                "F2": st.column_config.TextColumn("F2 (%)", help="Incidenza budget target")
            }
        )
        st.markdown("""
        <small>**Nota:** F1 = % aiuti target su tot. aiuti | F2 = % budget target su budget totale</small>
        """, unsafe_allow_html=True)      

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
