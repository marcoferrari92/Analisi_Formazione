import pandas as pd
import streamlit as st
import io



# *********
# LOADING 
# *********

"""
Carica i dati RNA e pulisce la colonna importi (rendendoli numeri).
"""

@st.cache_data
def load_rna_data(file):
    
    # Caricamento file
    df = pd.read_csv(file, sep=';', encoding='utf-8-sig', low_memory=False)
    
    # Pulizia colonna importo (trasforma stringa con virgola in numero)
    if 'RNA_ELEMENTO_DI_AIUTO' in df.columns:
        df['RNA_ELEMENTO_DI_AIUTO'] = pd.to_numeric(
            df['RNA_ELEMENTO_DI_AIUTO'].astype(str).str.replace(',', '.'), 
            errors='coerce'
        ).fillna(0)
        
    return df



# ****************
# RICERCA TARGETS
# ****************
"""
Controlla se almeno una keyword è presente in una delle colonne 
definite nei settings per la riga data.
"""

import re
from settings import COLONNE_RICERCA 

def is_target_row(row, keywords):
    
    # Creiamo un unico testo che unisce il contenuto delle colonne scelte
    testo_da_analizzare = " ".join([
        str(row[col]).upper() 
        for col in COLONNE_RICERCA 
        if col in row
    ])
    
    for k in keywords:
        # Costruiamo il pattern: \bKEYWORD\b
        # re.escape serve per evitare che caratteri speciali nella keyword (es. .) rompano la regex
        pattern = rf"\b{re.escape(k)}\b"
        
        if re.search(pattern, testo_da_analizzare):
            return True
            
    return False




def render_database_misure(df_rna):
    # Avvolgiamo tutto il contenuto dentro un expander
    st.subheader("🗄️ Database Bandi")
    with st.expander("Elenco degli aiuti", expanded=False):
        
        st.markdown("""
        Questa sezione raggruppa tutti i bandi trovati nel file RNA, indicando quante aziende li hanno utilizzati 
        e il volume economico totale per ogni singolo aiuto.
        """)

        # 1. Elaborazione dati: raggruppamento per Misura
        df_rna['importo_numerico'] = pd.to_numeric(
            df_rna['RNA_IMPORTO'].astype(str).str.replace(',', '.'), 
            errors='coerce'
        ).fillna(0)

        db_misure = df_rna.groupby('RNA_MISURA').agg({
            'RAGIONE SOCIALE': 'nunique', 
            'RNA_MISURA': 'count',        
            'importo_numerico': 'sum'     
        }).rename(columns={
            'RAGIONE SOCIALE': 'Aziende_Coinvolte',
            'RNA_MISURA': 'Numero_Erogazioni',
            'importo_numerico': 'Valore_Totale_€'
        }).reset_index()

        # 2. Ordinamento
        db_misure = db_misure.sort_values(by='Numero_Erogazioni', ascending=False)

        # 3. Visualizzazione Statistiche Veloci (ridotte per stare dentro l'expander)
        m1, m2 = st.columns(2)
        m1.metric("Misure Univoche", len(db_misure))
        m2.metric("Volume Totale", f"€ {db_misure['Valore_Totale_€'].sum():,.0f}")

        # 4. Tabella interattiva
        st.dataframe(
            db_misure,
            column_config={
                "RNA_MISURA": st.column_config.TextColumn("Nome della Misura / Bando"),
                "Valore_Totale_€": st.column_config.NumberColumn(format="%.2f €"),
                "Aziende_Coinvolte": "N. Aziende",
                "Numero_Erogazioni": "N. Totale Aiuti"
            },
            hide_index=True,
            use_container_width=True
        )

        # 5. Pulsante di Download
        csv_misure = io.BytesIO()
        db_misure.to_csv(csv_misure, index=False, sep=';', encoding='utf-8-sig')
        
        st.download_button(
            label="💾 Scarica Database Misure Univoche (CSV)",
            data=csv_misure.getvalue(),
            file_name="Database_Misure_RNA.csv",
            mime="text/csv",
            use_container_width=True
        )




import pdfplumber

def verifica_stato_clienti(df_rna, uploaded_clienti):
    """
    Estrae P.IVA/CF da qualsiasi file e aggiorna il database RNA.
    """
    try:
        lista_piva_clienti = set()
        # Regex per P.IVA (11 cifre) e Codici Fiscali (16 caratteri)
        regex_piva_cf = r'\b\d{11}\b|\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b'
        
        anteprima_debug = [] 

        # --- 1. ESTRAZIONE DATI (PDF o CSV) ---
        if uploaded_clienti.name.lower().endswith('.pdf'):
            with st.spinner("Analisi del PDF..."):
                with pdfplumber.open(uploaded_clienti) as pdf:
                    for page in pdf.pages:
                        # Estrazione tabelle
                        table = page.extract_table()
                        if table:
                            if not anteprima_debug: anteprima_debug = table[:10]
                            for row in table:
                                for cell in row:
                                    if cell:
                                        matches = re.findall(regex_piva_cf, str(cell).strip())
                                        lista_piva_clienti.update(matches)
                        
                        # Estrazione testo (per sicurezza se le tabelle falliscono)
                        testo_libero = page.extract_text() or ""
                        lista_piva_clienti.update(re.findall(regex_piva_cf, testo_libero))
        else:
            # Gestione CSV: leggiamo tutto il file come stringhe e cerchiamo i pattern
            df_temp = pd.read_csv(uploaded_clienti, sep=None, engine='python', dtype=str).fillna('')
            anteprima_debug = df_temp.head(10)
            for col in df_temp.columns:
                for val in df_temp[col]:
                    lista_piva_clienti.update(re.findall(regex_piva_cf, str(val)))

        # --- 2. DEBUG SIDEBAR ---
        with st.sidebar.expander("🔍 Verifica estrazione dati"):
            st.write(f"**File:** {uploaded_clienti.name}")
            st.write(f"**Identificativi trovati:** {len(lista_piva_clienti)}")
            if lista_piva_clienti:
                st.write("**Esempio:**", list(lista_piva_clienti)[:5])

        # --- 3. MATCHING SUL DATAFRAME RNA ---
        if not lista_piva_clienti:
            st.warning(f"Nessun codice identificativo trovato in {uploaded_clienti.name}")
            df_rna['STATO'] = "⚪ PROSPECT" # Default se non trova nulla
            return df_rna

        # Funzione di confronto pulita
        def check_match(valore_rna):
            # Pulizia del dato nel tuo database principale
            codice_pulito = str(valore_rna).strip().upper()
            return "🟢 MATCH" if codice_pulito in lista_piva_clienti else "⚪ PROSPECT"

        # AGGIORNAMENTO COLONNA STATO
        # Assicurati che 'RNA_CODICE_FISCALE_BENEFICIARIO' sia il nome corretto della colonna nel tuo df_rna
        if 'RNA_CODICE_FISCALE_BENEFICIARIO' in df_rna.columns:
            df_rna['STATO'] = df_rna['RNA_CODICE_FISCALE_BENEFICIARIO'].apply(check_match)
            st.success(f"Confronto completato: {len(df_rna[df_rna['STATO'] == '🟢 MATCH'])} match trovati.")
        else:
            st.error("La colonna 'RNA_CODICE_FISCALE_BENEFICIARIO' non esiste nel database RNA.")
        
        return df_rna

    except Exception as e:
        st.error(f"Errore: {e}")
        return df_rna


def genera_output_confronto(df_filtrato, uploaded_clienti):
    
    try:
        # 1. Creiamo il set di P.IVA/CF presenti nel report RNA
        piva_presenti_nel_periodo = set(
            df_filtrato['RNA_CODICE_FISCALE_BENEFICIARIO']
            .astype(str).str.strip().str.upper().unique()
        )

        # 2. Caricamento del file originale
        if uploaded_clienti.name.lower().endswith('.pdf'):
            with pdfplumber.open(uploaded_clienti) as pdf:
                all_data = []
                for page in pdf.pages:
                    # Usiamo impostazioni più aggressive per forzare la separazione delle colonne
                    table = page.extract_table(table_settings={
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_y_tolerance": 5,
                    })
                    if table:
                        all_data.extend(table)
                
                if not all_data: return None
                
                # Creiamo il DF
                df_tuo = pd.DataFrame(all_data[1:], columns=all_data[0])
                
                # --- LOGICA DI RIPARAZIONE (Se le colonne sono agglomerate) ---
                if len(df_tuo.columns) < 3:
                    st.warning("⚠️ Formato PDF complesso rilevato: applicazione split automatico delle colonne.")
                    # Regex per separare: [Progressivo] [Ragione Sociale] [P.IVA/CF] [Resto]
                    regex_split = r'^(\S+)\s+(.+?)\s+(\d{11}|[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\s+(.*)$'
                    
                    rows_fixed = []
                    col_name = df_tuo.columns[0]
                    for val in df_tuo[col_name].astype(str):
                        match = re.search(regex_split, val.strip())
                        if match:
                            rows_fixed.append(list(match.groups()))
                        else:
                            # Se non matcha perfettamente, proviamo a salvare il dato
                            rows_fixed.append([val, "", "", ""])
                    
                    df_tuo = pd.DataFrame(rows_fixed, columns=["PROGRESSIVO", "DENOMINAZIONE", "P.IVA/C.F.", "ALTRI DATI"])
        else:
            df_tuo = pd.read_csv(uploaded_clienti, sep=None, engine='python', dtype=str).fillna('')

        # 3. IDENTIFICAZIONE COLONNA IDENTIFICATIVI
        regex_identificativo = r'\b\d{11}\b|\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b'
        col_piva_tua = None
        for col in df_tuo.columns:
            sample = " ".join(df_tuo[col].astype(str).head(10)).upper()
            if re.search(regex_identificativo, sample):
                col_piva_tua = col
                break

        if not col_piva_tua:
            st.error("Impossibile trovare la colonna identificativi nel file.")
            return None

        # 4. LOGICA DI VERIFICA
        def verifica_presenza(val):
            if not val: return "NON TROVATO"
            match = re.search(regex_identificativo, str(val).upper())
            if match:
                if match.group(0) in piva_presenti_nel_periodo:
                    return "MATCH"
            return "NON TROVATO"

        # Aggiungiamo l'esito
        df_tuo['ESITO_AIUTI_RNA'] = df_tuo[col_piva_tua].apply(verifica_presenza)
        
        # Ordiniamo per mettere i match in alto
        df_tuo = df_tuo.sort_values(by='ESITO_AIUTI_RNA', ascending=True)
        
        return df_tuo

    except Exception as e:
        st.error(f"Errore nel confronto: {e}")
        return None


def colora_clienti(row):
    # Definiamo il colore: verde chiaro per i clienti
    # Il codice HEX #d4edda è il classico verde "success"
    color = 'background-color: #d4edda' if "CLIENTE" in str(row['STATO']) else ''
    return [color] * len(row)



def format_it(val):
    return f"€ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_pct(val):
    return f"{val:.1f}%".replace('.', ',')
