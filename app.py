# app.py
# Versione completa compatibile con nuovi campi RNA
# Mantiene KPI, benchmark, ranking, dettaglio azienda, download, grafici

import streamlit as st
import pandas as pd
import io
import plotly.express as px

from utils import render_database_misure, verifica_stato_clienti, colora_clienti

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="RNA Business Intelligence", layout="wide")

st.title("📊 Analizzatore Registro Nazionale Aiuti")
st.markdown("Analisi strategica e qualificazione lead basata sui dati ufficiali RNA.")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("1. Caricamento Dati")

uploaded_file = st.sidebar.file_uploader(
    "Carica file RNA (CSV estratto)",
    type=["csv"]
)

uploaded_clienti = st.sidebar.file_uploader(
    "Carica Database Clienti (Opzionale)",
    type=["csv"]
)

st.sidebar.header("2. Filtri Target")

default_kw = "formazione, competenze, corso, training"
keywords_raw = st.sidebar.text_area(
    "Parole chiave target",
    value=default_kw
)

btn_ricerca = st.sidebar.button(
    "🔍 Aggiorna Analisi",
    use_container_width=True,
    type="primary"
)

st.sidebar.header("3. Ordinamento")

sort_options = {
    "Numero Aiuti Target": "N_AIUTI_TARGET",
    "Valore Aiuti Target (€)": "VALORE_TARGET_€",
    "Incidenza Numero (%)": "INCIDENZA_N_TARGET_%",
    "Incidenza Volume (%)": "INCIDENZA_VOL_TARGET_%",
    "Valore Totale (€)": "VALORE_TOTALE_€",
    "Numero Totale Aiuti": "N_TOT_AIUTI"
}

sort_choice = st.sidebar.selectbox(
    "Ordina tabella per:",
    list(sort_options.keys()),
    index=0
)

# =====================================================
# FUNZIONI
# =====================================================

@st.cache_data
def load_data(file):
    df = pd.read_csv(
        file,
        sep=';',
        encoding='utf-8-sig',
        low_memory=False
    )

    # Mapping automatico nuovi campi -> campi usati dalla dashboard
    mapping = {
        'RNA_TITOLO_MISURA': 'RNA_MISURA',
        'RNA_DATA_CONCESSIONE': 'RNA_DATA',
        'RNA_CODICE_FISCALE_BENEFICIARIO': 'RNA_PIVA',
        'RNA_ELEMENTO_DI_AIUTO': 'RNA_IMPORTO',
        'RNA_IMPORTO_NOMINALE': 'RNA_IMPORTO',
        'RNA_DES_STRUMENTO': 'RNA_STRUMENTO'
    }

    for old, new in mapping.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    # Colonne minime
    required = ['RAGIONE SOCIALE']
    for c in required:
        if c not in df.columns:
            raise Exception(f"Colonna mancante: {c}")

    # Se mancanti le creo vuote
    for c in ['RNA_MISURA', 'RNA_DATA', 'RNA_PIVA', 'RNA_IMPORTO']:
        if c not in df.columns:
            df[c] = ''

    return df

def prepara_importi(df):
    df['RNA_IMPORTO'] = pd.to_numeric(
        df['RNA_IMPORTO']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False),
        errors='coerce'
    ).fillna(0)

    return df

def crea_target(df, keywords_raw):
    keywords = [k.strip().upper() for k in keywords_raw.split(',') if k.strip()]

    def is_target(text):
        txt = str(text).upper()
        return any(k in txt for k in keywords)

    df['is_target'] = df['RNA_MISURA'].apply(is_target)
    df['importo_target'] = df.apply(
        lambda x: x['RNA_IMPORTO'] if x['is_target'] else 0,
        axis=1
    )

    return df

def genera_report(df):
    escluse = [
        'RNA_DATA',
        'RNA_MISURA',
        'RNA_IMPORTO',
        'RNA_STRUMENTO',
        'is_target',
        'importo_target'
    ]

    col_ana = [
        c for c in df.columns
        if c not in escluse and c != 'RAGIONE SOCIALE'
    ]

    report = df.groupby('RAGIONE SOCIALE').agg({
        **{c: 'first' for c in col_ana},
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

    report['INCIDENZA_N_TARGET_%'] = (
        report['N_AIUTI_TARGET'] /
        report['N_TOT_AIUTI'] * 100
    ).fillna(0)

    report['INCIDENZA_VOL_TARGET_%'] = (
        report['VALORE_TARGET_€'] /
        report['VALORE_TOTALE_€'] * 100
    ).fillna(0)

    # Ranking
    ranks = {
        'RANK_VOL_TOT': 'VALORE_TOTALE_€',
        'RANK_VOL_TARGET': 'VALORE_TARGET_€',
        'RANK_N_TOT': 'N_TOT_AIUTI',
        'RANK_N_TARGET': 'N_AIUTI_TARGET',
        'RANK_INC_N': 'INCIDENZA_N_TARGET_%',
        'RANK_INC_VOL': 'INCIDENZA_VOL_TARGET_%'
    }

    for rk, col in ranks.items():
        report[rk] = report[col].rank(
            ascending=False,
            method='min'
        ).astype(int)

    return report

# =====================================================
# APP
# =====================================================

if uploaded_file is not None:

    try:
        df_raw = load_data(uploaded_file)
        df_raw = prepara_importi(df_raw)

        # Stato clienti
        if uploaded_clienti is not None:
            df_raw = verifica_stato_clienti(df_raw, uploaded_clienti)
        else:
            if 'STATO' not in df_raw.columns:
                df_raw['STATO'] = '⚪ PROSPECT'

        # Target
        df_raw = crea_target(df_raw, keywords_raw)

        # Report
        report = genera_report(df_raw)
        report = report.sort_values(
            by=sort_options[sort_choice],
            ascending=False
        )

        # =================================================
        # DATABASE MISURE
        # =================================================
        st.divider()
        render_database_misure(df_raw)

        # =================================================
        # KPI
        # =================================================
        st.divider()
        st.subheader("📋 Report Riepilogativo")

        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Aziende Totali", len(report))
        k2.metric(
            "Volume Totale",
            f"€ {report['VALORE_TOTALE_€'].sum():,.0f}"
        )
        k3.metric(
            "Bandi Target",
            int(report['N_AIUTI_TARGET'].sum())
        )
        k4.metric(
            "Volume Target",
            f"€ {report['VALORE_TARGET_€'].sum():,.0f}"
        )

        st.dataframe(
            report.style.apply(colora_clienti, axis=1),
            hide_index=True,
            use_container_width=True
        )

        # =================================================
        # BENCHMARK
        # =================================================
        with st.expander("📊 Analisi Benchmark di Mercato", expanded=True):

            attive = report[
                report['INCIDENZA_VOL_TARGET_%'] > 0
            ].copy()

            media = attive['INCIDENZA_VOL_TARGET_%'].mean() if not attive.empty else 0
            mediana = attive['INCIDENZA_VOL_TARGET_%'].median() if not attive.empty else 0

            b1, b2, b3 = st.columns(3)
            b1.metric("Media", f"{media:.2f}%")
            b2.metric("Mediana", f"{mediana:.2f}%")
            b3.metric("Aziende Attive", len(attive))

            fig = px.box(
                attive,
                x="INCIDENZA_VOL_TARGET_%",
                orientation='h',
                points='all',
                hover_name='RAGIONE SOCIALE',
                template='plotly_white'
            )
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

            # Lead prioritari
            st.write("### 🚀 Lead Prioritari")

            lead = report[
                (report['STATO'].astype(str).str.contains('PROSPECT')) &
                (report['INCIDENZA_VOL_TARGET_%'] < mediana)
            ].copy()

            lead['GAP_POTENZIALE_€'] = (
                lead['VALORE_TOTALE_€'] * mediana / 100
                - lead['VALORE_TARGET_€']
            ).clip(lower=0)

            st.dataframe(
                lead[
                    [
                        'RAGIONE SOCIALE',
                        'VALORE_TOTALE_€',
                        'INCIDENZA_VOL_TARGET_%',
                        'GAP_POTENZIALE_€'
                    ]
                ],
                hide_index=True,
                use_container_width=True
            )

        # =================================================
        # DETTAGLIO AZIENDA
        # =================================================
        st.divider()
        st.subheader("🎯 Analisi Dettagliata Azienda")

        search_txt = st.text_input(
            "Inserisci Ragione Sociale"
        )

        if search_txt:

            azienda = df_raw[
                df_raw['RAGIONE SOCIALE']
                .str.contains(search_txt, case=False, na=False)
            ].copy()

            if not azienda.empty:

                nome = azienda['RAGIONE SOCIALE'].iloc[0]
                info = report[
                    report['RAGIONE SOCIALE'] == nome
                ].iloc[0]

                st.info(f"### 🏢 {nome}")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "% Incidenza N.",
                        f"{info['INCIDENZA_N_TARGET_%']:.1f}%"
                    )
                    st.metric(
                        "% Incidenza Vol.",
                        f"{info['INCIDENZA_VOL_TARGET_%']:.1f}%"
                    )

                with c2:
                    st.metric(
                        "Volume Totale",
                        f"€ {info['VALORE_TOTALE_€']:,.0f}"
                    )
                    st.metric(
                        "Volume Target",
                        f"€ {info['VALORE_TARGET_€']:,.0f}"
                    )

                with c3:
                    st.metric(
                        "Bandi Totali",
                        int(info['N_TOT_AIUTI'])
                    )
                    st.metric(
                        "Bandi Target",
                        int(info['N_AIUTI_TARGET'])
                    )

                # colonne prioritarie
                priorita = [
                    'RNA_DATA',
                    'RNA_CAR',
                    'RNA_MISURA',
                    'RNA_TITOLO_PROGETTO',
                    'RNA_IMPORTO',
                    'is_target'
                ]

                altre = [
                    c for c in azienda.columns
                    if c.startswith('RNA_')
                    and c not in priorita
                ]

                cols = [c for c in priorita if c in azienda.columns] + altre

                st.dataframe(
                    azienda[cols].style.apply(
                        lambda r: [
                            'background-color:#d4edda'
                            if r['is_target'] else ''
                        ] * len(r),
                        axis=1
                    ),
                    hide_index=True,
                    use_container_width=True
                )

            else:
                st.warning("Nessuna azienda trovata.")

        # =================================================
        # SCATTER
        # =================================================
        st.divider()
        st.subheader("📈 Correlazione")

        st.scatter_chart(
            report,
            x='VALORE_TARGET_€',
            y='VALORE_TOTALE_€',
            size='N_TOT_AIUTI',
            use_container_width=True
        )

        # =================================================
        # DOWNLOAD
        # =================================================
        csv_buffer = io.BytesIO()
        report.to_csv(
            csv_buffer,
            index=False,
            sep=';',
            encoding='utf-8-sig'
        )

        st.sidebar.download_button(
            "💾 Scarica Report CSV",
            csv_buffer.getvalue(),
            "Analisi_RNA.csv",
            "text/csv",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Errore: {e}")

else:
    st.info("👋 Carica il file CSV per iniziare.")
