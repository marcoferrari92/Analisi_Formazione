import pandas as pd
import streamlit as st
import io

import plotly.express as px

def render_database_misure(df_rna):
    st.subheader("📋 Database degli Aiuti")
    st.markdown("""
    Questa sezione raggruppa tutti i bandi trovati nel file RNA, indicando quante aziende li hanno utilizzati 
    e il volume economico totale per ogni singolo aiuto.
    """)

    # 1. Elaborazione dati: raggruppamento per Misura
    df_temp = df_rna.copy()
    df_temp['importo_numerico'] = pd.to_numeric(
        df_temp['RNA_IMPORTO'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    ).fillna(0)

    db_misure = df_temp.groupby('RNA_MISURA').agg({
        'RAGIONE SOCIALE': 'nunique', # Numero di aziende uniche
        'RNA_MISURA': 'count',        # Numero di erogazioni totali
        'importo_numerico': 'sum'     # Valore totale erogato
    }).rename(columns={
        'RAGIONE SOCIALE': 'Aziende_Coinvolte',
        'RNA_MISURA': 'Numero_Erogazioni',
        'importo_numerico': 'Valore_Totale_€'
    }).reset_index()

    # Ordinamento base per popolarità
    db_misure = db_misure.sort_values(by='Numero_Erogazioni', ascending=False)

    # 2. Visualizzazione Statistiche Veloci
    m1, m2 = st.columns(2)
    m1.metric("Misure Univoche Trovate", len(db_misure))
    m2.metric("Volume Economico Totale", f"€ {db_misure['Valore_Totale_€'].sum():,.0f}")

    # --- 3. SEZIONE GRAFICI INTERATTIVI ---
    st.write("### 📊 Analisi Visuale del Mercato")
    tab1, tab2, tab3 = st.tabs(["💰 Top per Budget", "🎯 Diffusione Misure", "📈 Matrice Opportunità"])

    with tab1:
        # Top 10 per Valore Economico
        top_valore = db_misure.sort_values(by='Valore_Totale_€', ascending=False).head(10)
        fig_val = px.bar(
            top_valore, 
            x='Valore_Totale_€', 
            y='RNA_MISURA', 
            orientation='h',
            title="Top 10 Bandi per Volume Economico (€)",
            labels={'Valore_Totale_€': 'Budget Totale (€)', 'RNA_MISURA': 'Nome Bando'},
            color='Valore_Totale_€',
            color_continuous_scale='Viridis'
        )
        fig_val.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_val, use_container_width=True)

    with tab2:
        # Treemap per vedere la frammentazione del mercato
        fig_tree = px.treemap(
            db_misure.head(20), 
            path=['RNA_MISURA'], 
            values='Numero_Erogazioni',
            title="Prime 20 Misure per Numero di Erogazioni",
            color='Numero_Erogazioni',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with tab3:
        # Scatter Plot: Rapporto tra numero aziende e budget
        fig_scatter = px.scatter(
            db_misure, 
            x='Aziende_Coinvolte', 
            y='Valore_Totale_€',
            size='Numero_Erogazioni',
            hover_name='RNA_MISURA',
            title="Relazione tra Numero Aziende e Budget Totale",
            labels={'Aziende_Coinvolte': 'N. Aziende Uniche', 'Valore_Totale_€': 'Volume Totale (€)'},
            color='Valore_Totale_€',
            log_y=True # Scala logaritmica per gestire le grandi differenze di budget
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # 4. Tabella interattiva
    st.write("### 🗄️ Dati Analitici")
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
        df_rna['RNA_PIVA_CLEAN'] = (
            df_rna['RNA_PIVA']
            .astype(str)
            .str.strip()
            .str.replace(' ', '')
        )

        # 4. Matching (Il confronto vero e proprio)
        # Se la P.IVA pulita è nella lista clienti -> CLIENTE, altrimenti PROSPECT
        df_rna['STATO'] = df_rna['RNA_PIVA_CLEAN'].apply(
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
