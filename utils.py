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
    # 1. Carichiamo tutto il file come stringhe (dtype=str) 
    # Questo è il modo più sicuro per non perdere mai gli zeri ovunque
    df = pd.read_csv(file, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # 2. Pulizia Identificativo (CF/PIVA)
    if 'RNA_CODICE_FISCALE_BENEFICIARIO' in df.columns:
        df['RNA_CODICE_FISCALE_BENEFICIARIO'] = (
            df['RNA_CODICE_FISCALE_BENEFICIARIO']
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True) # Rimuove .0 se presente
            .str.zfill(11)                        # Forza 11 cifre (ripristina lo zero)
        )
    
    # 3. Pulizia Importo (Converte in numero per i calcoli)
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




def verifica_stato_clienti(df_rna, uploaded_clienti):
    """
    Estrae P.IVA/CF in modo robusto e aggiorna il database RNA.
    """
    try:
        lista_piva_clienti = set()
        
        # --- 1. ESTRAZIONE DATI ---
        if uploaded_clienti.name.lower().endswith('.pdf'):
            # (Manteniamo la logica PDF con Regex perché lì il testo è libero)
            regex_piva_cf = r'\b\d{10,11}\b|\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b'
            with st.spinner("Analisi del PDF..."):
                with pdfplumber.open(uploaded_clienti) as pdf:
                    for page in pdf.pages:
                        testo = page.extract_text() or ""
                        lista_piva_clienti.update(re.findall(regex_piva_cf, testo))
        else:
            # --- GESTIONE CSV (IL TUO CASO) ---
            # Leggiamo il CSV puntando direttamente alle colonne giuste
            df_temp = pd.read_csv(uploaded_clienti, sep=';', dtype=str).fillna('')
            df_temp.columns = [c.strip().upper() for c in df_temp.columns]
            
            # Funzione per pulire e normalizzare (fondamentale per i match)
            def pulisci_dato(valore):
                s = str(valore).strip().split('.')[0]
                if s.isdigit() and len(s) < 11:
                    return s.zfill(11) # Aggiunge lo zero se serve per il match con RNA
                return s.upper()

            if 'PARTITA IVA' in df_temp.columns:
                pive = df_temp['PARTITA IVA'].apply(pulisci_dato).unique()
                lista_piva_clienti.update(pive)
            
            if 'CODICE FISCALE' in df_temp.columns:
                cf = df_temp['CODICE FISCALE'].apply(pulisci_dato).unique()
                lista_piva_clienti.update(cf)

        # Rimuoviamo eventuali stringhe vuote
        lista_piva_clienti.discard('')

        # --- 2. DEBUG ---
        with st.sidebar.expander("🔍 Verifica estrazione dati"):
            st.write(f"**Identificativi trovati:** {len(lista_piva_clienti)}")
            st.write("**Esempi estratti:**", list(lista_piva_clienti)[:5])

        # --- 3. MATCHING SUL DATAFRAME RNA ---
        if not lista_piva_clienti:
            st.warning("Nessun codice trovato nel file caricato.")
            df_rna['STATO'] = "⚪ PROSPECT"
            return df_rna

        # Applichiamo il confronto normalizzando anche il DB RNA
        def check_match(valore_rna):
            codice_db = str(valore_rna).strip().upper()
            # Se il codice nel DB RNA è numerico e corto, mettiamo lo zero per confrontarlo
            if codice_db.isdigit() and len(codice_db) < 11:
                codice_db = codice_db.zfill(11)
            
            return "🟢 MATCH" if codice_db in lista_piva_clienti else "⚪ PROSPECT"

        if 'RNA_CODICE_FISCALE_BENEFICIARIO' in df_rna.columns:
            df_rna['STATO'] = df_rna['RNA_CODICE_FISCALE_BENEFICIARIO'].apply(check_match)
            n_match = len(df_rna[df_rna['STATO'] == '🟢 MATCH'])
            st.success(f"Confronto completato: {n_match} match trovati.")
        else:
            st.error("Colonna 'RNA_CODICE_FISCALE_BENEFICIARIO' non trovata nel DB RNA.")
        
        return df_rna

    except Exception as e:
        st.error(f"Errore durante la verifica: {e}")
        return df_rna




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





def genera_output_confronto_csv(df_filtrato, uploaded_clienti):  
    import re  
    import pandas as pd  
    import streamlit as st  
    import io  

    try:  
        # 1. Preparazione set di confronto (RNA)  
        piva_presenti_nel_periodo = set(  
            df_filtrato['RNA_CODICE_FISCALE_BENEFICIARIO']  
            .astype(str).str.strip().str.upper().unique()  
        )  

        # 2. CARICAMENTO DATI CSV (MANTENIAMO TUTTO)
        content = uploaded_clienti.getvalue().decode('utf-8-sig')  
        
        # Determiniamo il separatore guardando la prima riga  
        first_line = content.split('\n')[0]  
        sep = ';' if ';' in first_line else ','  
        
        # Carichiamo il DataFrame integrale  
        df_tuo = pd.read_csv(io.StringIO(content), sep=sep, dtype=str, engine='python').fillna('')  

        # 3. IDENTIFICAZIONE DELLA COLONNA PER IL MATCH  
        regex_id = r'\b\d{11}\b|\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b'  
        col_piva_tua = None  
        
        # Priorità a nomi colonna noti  
        for col in df_tuo.columns:  
            if any(x in str(col).upper() for x in ["PARTITA IVA", "CODICE FISCALE", "P.IVA", "P. IVA", "C.F."]):  
                col_piva_tua = col  
                break  
        
        # Fallback: scansione contenuto  
        if not col_piva_tua:  
            for col in df_tuo.columns:  
                if df_tuo[col].astype(str).str.contains(regex_id, regex=True).any():  
                    col_piva_tua = col  
                    break  

        if not col_piva_tua:  
            st.error("⚠️ Non ho trovato una colonna P.IVA o C.F. nel tuo file CSV.")  
            return None  

        # 4. AGGIUNTA COLONNA MATCH  
        def verifica(val):  
            val_str = str(val).strip().upper()  
            match = re.search(regex_id, val_str)  
            if match:  
                if match.group(0) in piva_presenti_nel_periodo:  
                    return "MATCH"  
            return "NON TROVATO"  

        df_tuo['ESITO_AIUTI_RNA'] = df_tuo[col_piva_tua].apply(verifica)  
        
        # Spostiamo la colonna esito in PRIMA posizione  
        cols = ['ESITO_AIUTI_RNA'] + [c for c in df_tuo.columns if c != 'ESITO_AIUTI_RNA']  
        df_tuo = df_tuo[cols]  
        
        return df_tuo  

    except Exception as e:  
        st.error(f"Errore nel confronto CSV: {e}")  
        return None


def genera_output_confronto_pdf(df_filtrato, uploaded_clienti):
    import re
    import pandas as pd
    import pdfplumber
    import streamlit as st

    try:
        # 1. Preparazione set di confronto (RNA)
        piva_presenti_nel_periodo = set(
            df_filtrato['RNA_CODICE_FISCALE_BENEFICIARIO']
            .astype(str).str.strip().str.upper().unique()
        )

        rows_list = []
        # Regex per identificare P.IVA (11 cifre) o CF (16 caratteri)
        regex_id = r'(\d{11}|[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])'

        # 2. Estrazione dati dal PDF (Logica "Blind" per evitare errori di colonna)
        with pdfplumber.open(uploaded_clienti) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        if not row: continue
                        
                        # Uniamo tutta la riga in una stringa unica per non impazzire con le colonne
                        line_text = " ".join([str(cell) for cell in row if cell is not None]).replace('\n', ' ')
                        
                        # Cerchiamo il codice (PIVA o CF) nella riga
                        match = re.search(regex_id, line_text)
                        codice = match.group(0) if match else ""
                        
                        if codice: # Aggiungiamo solo se abbiamo trovato un codice
                            rows_list.append({
                                "DATI_ORIGINALI": line_text,
                                "IDENTIFICATIVO_ESTRATTO": codice,
                                "ESITO_AIUTI_RNA": "MATCH" if codice.upper() in piva_presenti_nel_periodo else "NON TROVATO"
                            })
        
        if not rows_list:
            st.warning("Nessun dato identificativo (P.IVA/CF) estratto dal PDF.")
            return None

        df_tuo = pd.DataFrame(rows_list)
        
        # Spostiamo l'esito all'inizio
        cols = ['ESITO_AIUTI_RNA'] + [c for c in df_tuo.columns if c != 'ESITO_AIUTI_RNA']
        df_tuo = df_tuo[cols]

        # Ordiniamo per mettere i MATCH in cima
        df_tuo = df_tuo.sort_values(by='ESITO_AIUTI_RNA', ascending=True)
        
        return df_tuo

    except Exception as e:
        st.error(f"Errore tecnico nel confronto PDF: {e}")
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




def crea_radar_azienda(row, med_Fo, med_Fe, med_aiuti_t, med_budget_t):
                
    # Categorie degli assi
    categories = ['Specializzazione (Fo)', 'Peso Economico (Fe)', 'Volume Aiuti', 'Budget Ricevuto']
    
    # Funzione di normalizzazione (1.0 = Mediana del settore)
    # Applichiamo un tetto a 3.0 per evitare che aziende enormi deformino il grafico
    def norm(val, med):
        if med == 0: return 0
        return min(val / med, 3.0) 

    # Valori dell'azienda specifica
    valori_azienda = [
        norm(row['Fo'], med_Fo),
        norm(row['Fe'], med_Fe),
        norm(row['Aiuti Target'], med_aiuti_t),
        norm(row['Budget Target'], med_budget_t)
    ]
    
    # Il benchmark è sempre 1.0 (la mediana)
    valori_benchmark = [1, 1, 1, 1]

    fig = go.Figure()

    # Traccia Area Azienda
    fig.add_trace(go.Scatterpolar(
        r=valori_azienda + [valori_azienda[0]], # Chiudiamo il cerchio
        theta=categories + [categories[0]],
        fill='toself',
        name=f"Profilo {row['Ragione Sociale'][:15]}...",
        line_color='#e74c3c',
        fillcolor='rgba(231, 76, 60, 0.4)'
    ))
    
    # Traccia Area Mediana (Benchmark)
    fig.add_trace(go.Scatterpolar(
        r=valori_benchmark + [valori_benchmark[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='Mediana Settore',
        line_color='#34495e',
        fillcolor='rgba(52, 73, 94, 0.1)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 3],
                tickvals=[1, 2, 3],
                ticktext=['Mediana', '2x', '3x+']
            )
        ),
        showlegend=True,
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig
