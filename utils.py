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
    Versione Universale: Legge CSV o PDF, identifica automaticamente la 
    colonna o il testo contenente P.IVA (11 cifre) e confronta con RNA.
    """
    try:
        lista_piva_clienti = set()
        regex_piva_pura = r'\b\d{11}\b' # Cerca 11 cifre esatte isolate

        # --- 1. CARICAMENTO E ESTRAZIONE DATI ---
        if uploaded_clienti.name.lower().endswith('.pdf'):
            with st.spinner("Analisi del PDF in corso..."):
                with pdfplumber.open(uploaded_clienti) as pdf:
                    testo_completo = ""
                    trovata_tabella = False
                    
                    for page in pdf.pages:
                        # Tentativo A: Estrazione tabelle
                        table = page.extract_table()
                        if table:
                            trovata_tabella = True
                            df_temp = pd.DataFrame(table)
                            # Per ogni cella della tabella, cerchiamo P.IVA
                            for col in df_temp.columns:
                                for val in df_temp[col]:
                                    clean_val = re.sub(r'\D', '', str(val))
                                    if len(clean_val) == 11:
                                        lista_piva_clienti.add(clean_val)
                        
                        # Tentativo B: Estrazione testo libero (se le tabelle falliscono o sono parziali)
                        testo_completo += page.extract_text() or ""

                    # Se non abbiamo trovato nulla nelle tabelle, cerchiamo nel testo libero
                    piva_nel_testo = re.findall(regex_piva_pura, testo_completo)
                    lista_piva_clienti.update(piva_nel_testo)

        else:
            # Gestione CSV/TXT
            df_clienti = pd.read_csv(uploaded_clienti, sep=None, engine='python', dtype=str).fillna('')
            
            col_trovata = None
            for col in df_clienti.columns:
                # Testiamo se la colonna contiene P.IVA (almeno il 60% dei valori)
                sample = df_clienti[col].str.replace(r'\D', '', regex=True).replace('', pd.NA).dropna().head(20)
                if not sample.empty:
                    matches = sample.apply(lambda x: len(str(x)) == 11).sum()
                    if matches > len(sample) * 0.6:
                        col_trovata = col
                        break
            
            if col_trovata:
                pivas = df_clienti[col_trovata].str.replace(r'\D', '', regex=True).unique()
                lista_piva_clienti.update([p for p in pivas if len(str(p)) == 11])

        # --- 2. VERIFICA RISULTATI ---
        if not lista_piva_clienti:
            st.error(f"⚠️ Nessuna Partita IVA valida (11 cifre) trovata in {uploaded_clienti.name}")
            return df_rna

        # --- 3. MATCHING CON DATAFRAME RNA ---
        def check_stato(val):
            # Normalizziamo il valore RNA (solo numeri)
            rna_val = re.sub(r'\D', '', str(val))
            return "🟢 CLIENTE" if rna_val in lista_piva_clienti else "⚪ PROSPECT"

        df_rna['STATO'] = df_rna['RNA_CODICE_FISCALE_BENEFICIARIO'].apply(check_stato)
        
        st.sidebar.success(f"✅ Analisi completata: {len(lista_piva_clienti)} P.IVA trovate.")
        return df_rna

    except Exception as e:
        st.error(f"❌ Errore critico durante l'elaborazione del file: {e}")
        return df_rna





def colora_clienti(row):
    # Definiamo il colore: verde chiaro per i clienti
    # Il codice HEX #d4edda è il classico verde "success"
    color = 'background-color: #d4edda' if "CLIENTE" in str(row['STATO']) else ''
    return [color] * len(row)



def format_it(val):
    return f"€ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_pct(val):
    return f"{val:.1f}%".replace('.', ',')
