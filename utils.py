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

# Importiamo la configurazione
from settings import COLONNE_RICERCA 

def is_target_row(row, keywords):

    # Creiamo un unico testo che unisce il contenuto delle colonne scelte
    testo_da_analizzare = " ".join([
        str(row[col]).upper() 
        for col in COLONNE_RICERCA 
        if col in row
    ])
    
    return any(k in testo_da_analizzare for k in keywords)




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



def verifica_stato_clienti(df_rna, uploaded_clienti):
    """
    Confronta il database RNA con il file Clienti tramite Partita IVA.
    Ritorna il dataframe RNA arricchito con la colonna 'STATO'.
    """
    try:
        # 1. Caricamento del file Clienti 2026 (separatore ;)
        # Usiamo 'low_memory=False' per gestire colonne con tipi misti
        df_clienti = pd.read_csv(uploaded_clienti, sep=';', encoding='utf-8-sig', low_memory=False)
        
        if 'Partita IVA' not in df_clienti.columns:
            st.error("⚠️ Errore: Colonna 'Partita IVA' non trovata nel file clienti!")
            return df_rna

        # 2. Pulizia e Normalizzazione P.IVA Clienti
        # Rimuoviamo spazi, rendiamo tutto stringa e togliamo eventuali prefissi
        lista_piva_clienti = (
            df_clienti['Partita IVA']
            .astype(str)
            .str.strip()
            .str.replace(' ', '')
            .unique()
            .tolist()
        )

        # 3. Pulizia P.IVA nel database RNA
        # Creiamo una versione pulita per il confronto
        df_rna['RNA_CODICE_FISCALE_BENEFICIARIO'] = (
            df_rna['RNA_CODICE_FISCALE_BENEFICIARIO']
            .astype(str)
            .str.strip()
            .str.replace(' ', '')
        )

        # 4. Matching (Il confronto vero e proprio)
        # Se la P.IVA pulita è nella lista clienti -> CLIENTE, altrimenti PROSPECT
        df_rna['STATO'] = df_rna['RNA_CODICE_FISCALE_BENEFICIARIO'].apply(
            lambda x: "🟢 CLIENTE" if x in lista_piva_clienti else "⚪ PROSPECT"
        )
        
        # Rimuoviamo la colonna di servizio per pulizia
        df_rna = df_rna.drop(columns=['RNA_PIVA_CLEAN'])
        
        st.sidebar.success(f"✅ Confronto completato: {len(lista_piva_clienti)} clienti caricati.")
        return df_rna

    except Exception as e:
        st.error(f"❌ Errore durante il confronto P.IVA: {e}")
        return df_rna


def colora_clienti(row):
    # Definiamo il colore: verde chiaro per i clienti
    # Il codice HEX #d4edda è il classico verde "success"
    color = 'background-color: #d4edda' if "CLIENTE" in str(row['STATO']) else ''
    return [color] * len(row)
