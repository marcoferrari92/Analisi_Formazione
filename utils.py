import pandas as pd
import streamlit as st
import io

def render_database_misure(df_rna):
    st.subheader("📋 Database degli Aiuti")
    st.markdown("""
    Questa sezione raggruppa tutti i bandi trovati nel file RNA, indicando quante aziende li hanno utilizzati 
    e il volume economico totale per ogni singolo aiuto.
    """)

    # 1. Elaborazione dati: raggruppamento per Misura
    # Convertiamo l'importo in numero per il calcolo
    df_rna['importo_numerico'] = pd.to_numeric(
        df_rna['RNA_IMPORTO'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    ).fillna(0)

    db_misure = df_rna.groupby('RNA_MISURA').agg({
        'RAGIONE SOCIALE': 'nunique', # Numero di aziende uniche
        'RNA_MISURA': 'count',        # Numero di erogazioni totali
        'importo_numerico': 'sum'     # Valore totale erogato
    }).rename(columns={
        'RAGIONE SOCIALE': 'Aziende_Coinvolte',
        'RNA_MISURA': 'Numero_Erogazioni',
        'importo_numerico': 'Valore_Totale_€'
    }).reset_index()

    # 2. Ordinamento per popolarità (più erogazioni in alto)
    db_misure = db_misure.sort_values(by='Numero_Erogazioni', ascending=False)

    # 3. Visualizzazione Statistiche Veloci
    m1, m2 = st.columns(2)
    m1.metric("Misure Univoche Trovate", len(db_misure))
    m2.metric("Volume Economico Totale", f"€ {db_misure['Valore_Totale_€'].sum():,.0f}")

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

    # 5. Pulsante di Download per il Database Misure
    csv_misure = io.BytesIO()
    db_misure.to_csv(csv_misure, index=False, sep=';', encoding='utf-8-sig')
    
    st.download_button(
        label="💾 Scarica Database Misure Univoche (CSV)",
        data=csv_misure.getvalue(),
        file_name="Database_Misure_RNA.csv",
        mime="text/csv",
        use_container_width=True
    )
