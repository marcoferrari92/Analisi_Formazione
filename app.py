import streamlit as st
import pandas as pd
import io
import plotly.express as px


# Caricamenti
from settings import DEFAULT_KEYWORDS
from utils import  load_rna_data, is_target_row, format_it, format_pct, render_database_misure, verifica_stato_clienti, colora_clienti
from analisi import create_centered_pie

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
with st.sidebar.popover("ℹ️ Info logica di ricerca"):
    st.markdown("""
    **Dove cerchiamo le parole chiave?**
    
    Il sistema analizza ogni riga del database RNA verificando la presenza delle tue keywords in queste colonne ufficiali:
    1. `RNA_TITOLO_MISURA`
    2. `RNA_DESCRIZIONE_PROGETTO`
    3. `RNA_TITOLO_PROGETTO`
    
    *La ricerca non è case-sensitive (non distingue tra maiuscole e minuscole).*
    """)

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
                
        st.divider();
        
        # RIEPILOGO
        
        # Famiglie di aziende
        aziende_totali        = set(df['RNA_CODICE_FISCALE_BENEFICIARIO'].unique())
        aziende_target        = set(df[df['IS_TARGET'] == 1]['RNA_CODICE_FISCALE_BENEFICIARIO'].unique())
        aziende_live          = set(df[df['RNA_ELEMENTO_DI_AIUTO'] > 0]['RNA_CODICE_FISCALE_BENEFICIARIO'].unique())
        aziende_dead          = aziende_totali - aziende_live
        aziende_off           = aziende_live - aziende_target
        
        n_aziende             = df['RNA_CODICE_FISCALE_BENEFICIARIO'].nunique()
        n_aziende_target      = len(aziende_target)
        n_aziende_live        = len(aziende_live)
        n_aziende_dead        = len(aziende_dead)
        n_aziende_off         = len(aziende_off)
        
        n_aiuti_totali        = len(df)
        n_aiuti_target        = df['IS_TARGET'].sum()
        
        budget_totale         = df['RNA_ELEMENTO_DI_AIUTO'].sum()
        budget_target         = df['IMPORTO_TARGET'].sum()
        #budget_medio          = budget_totale/n_aziende_live
        #budget_target_medio   = budget_target/n_aziende_target
        
        perc_aiuti_target     = (n_aiuti_target / n_aiuti_totali * 100) if n_aiuti_totali > 0 else 0
        perc_budget_target    = (budget_target / budget_totale * 100) if budget_totale > 0 else 0


        # PANORAMICA SETTORE TARGET ******************************
        
        # Periodo temporale (YYYY-MM-DD)
        df['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df['RNA_DATA_CONCESSIONE'], errors='coerce')
        data_min = df['RNA_DATA_CONCESSIONE'].min().strftime('%d/%m/%Y') if not df['RNA_DATA_CONCESSIONE'].dropna().empty else "N/D"
        data_max = df['RNA_DATA_CONCESSIONE'].max().strftime('%d/%m/%Y') if not df['RNA_DATA_CONCESSIONE'].dropna().empty else "N/D"

        st.subheader("🎯 Panoramica Settore Target")
        st.info(f"📅 **Periodo Analizzato:** dal {data_min} al {data_max}")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Aziende Attive", f"{n_aziende_live}")
            st.metric("Aziende Target", f"{n_aziende_target}", 
                      delta=f"{(n_aziende_target/n_aziende)*100:.1f}% del totale", delta_color = "normal")
        with m2:
            st.metric("Totale Aiuti", f"{n_aiuti_totali}")
            st.metric("Aiuti Target", f"{n_aiuti_target}",delta=f"{perc_aiuti_target:.1f}% del totale")
            
            
        with m3:
            st.metric("Budget Totale", f"€ {budget_totale:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            st.metric("Budget Target",
                      f"€ {budget_target:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                     delta=f"{perc_budget_target:.1f}% del budget totale")

        # GRAFICI A TORTA 
        with m1:
            st.write("")
            st.plotly_chart(create_centered_pie([n_aziende_target, n_aziende - n_aziende_target]), 
                    use_container_width=True, 
                    config={'displayModeBar': False})
            st.caption("**Aziende Target**: Aziende attive nel settore target (budget target > 0€)")

        with m2:
            st.write("")
            st.plotly_chart(create_centered_pie([n_aiuti_target, n_aiuti_totali - n_aiuti_target]), 
                    use_container_width=True, 
                    config={'displayModeBar': False})

        with m3:
            st.write("")
            st.plotly_chart(create_centered_pie([budget_target, budget_totale - budget_target]), 
                    use_container_width=True, 
                    config={'displayModeBar': False})

        
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

        # --- 3. CALCOLO Fo e Fe  ---
        report_aziende['Fo'] = (report_aziende['IS_TARGET'] / report_aziende['RNA_TITOLO_MISURA'] * 100).fillna(0)
        report_aziende['Fe'] = (report_aziende['IMPORTO_TARGET'] / report_aziende['RNA_ELEMENTO_DI_AIUTO'] * 100).fillna(0)

        # --- 4. RINOMINA ---
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

        # --- 5. TABELLA  ---
        st.write("")
        st.dataframe(
            report_aziende.style.apply(colora_clienti, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "P.IVA": st.column_config.TextColumn("P.IVA"),
                "Ragione Sociale": st.column_config.TextColumn("Ragione Sociale", width="large"),
                "Aiuti": st.column_config.NumberColumn("Aiuti", format="%d"),
                "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d"),
        
                # Formattazione Budget (mantiene il sorting numerico)
                "Budget": st.column_config.NumberColumn(
                    "Budget Totale (€)",
                    format="%.2f", # Streamlit userà il separatore locale del browser (italiano se impostato)
                ),
                "Budget Target": st.column_config.NumberColumn(
                    "Budget Target (€)",
                    format="%.2f",
                ),
        
                # Formattazione Percentuali Fo e Fe
                "Fo": st.column_config.NumberColumn(
                    "Fo (%)",
                    format="%.1f%%", # Aggiunge il simbolo % ma resta un numero per il sorting
                    help="Incidenza numero aiuti target"
                ),
                "Fe": st.column_config.NumberColumn(
                    "Fe (%)",
                    format="%.1f%%",
                    help="Incidenza budget target"
                )
            }
        )
        st.markdown("""
        <small>**Nota:** Fo = % aiuti target su tot. aiuti | Fe = % budget target su budget totale</small>
        """, unsafe_allow_html=True)      
        st.write("")

        
        # --- 1. CALCOLO BENCHMARK (Solo su aziende con attività Target) ---
        # Usiamo il report_aziende creato precedentemente
        df_benchmark_1 = report_aziende[report_aziende['Budget Target'] > 0]
        df_benchmark_2 = report_aziende[report_aziende['Budget'] > 0]

        if not df_benchmark_1.empty:
            med_aiuti              = df_benchmark_2['Aiuti'].median()
            med_budget             = df_benchmark_2['Budget'].median()
            med_budget_target      = df_benchmark_1['Budget Target'].median()
            med_aiuti_target       = df_benchmark_1['Aiuti Target'].median()
            med_Fo                 = df_benchmark_1['Fo'].median()
            med_Fe                 = df_benchmark_1['Fe'].median()

            # --- 2. UI: RIQUADRO BENCHMARK ---
            st.subheader("📈 Benchmark Settore Target")

            # Menu a scomparsa con la spiegazione tecnica e metodologica
            with st.expander("📖 Guida alla lettura e Metodologia"):
                st.markdown("""
                    Il benchmark permette di confrontare la singola azienda con la **"linea di mezzo (mediana)"** del mercato di riferimento. 

                    ### 📊 Cos'è la Mediana?
                    A differenza della media (che può essere influenzata da pochi valori estremi, come un'azienda che riceve milioni di euro), la **Mediana** è il valore che divide esattamente in due la popolazione: il 50% delle aziende si trova sopra questo valore e il 50% sotto. 
                    Rappresenta quindi l'**azienda tipica** del settore: se un'azienda è sotto la mediana, significa che sta ottenendo meno della metà dei suoi competitor diretti.

                    ### 🌍 Indicatori del Mercato (Potenziale)
                    Questi valori descrivono l'ambiente esterno e la taglia degli incentivi disponibili.
                    * **Numero Aiuti per Azienda (Frequenza Operativa):** Indica quanti progetti di finanza agevolata le aziende hanno ricevuto mediamente nel periodo considerato. Una mediana alta indica un settore dinamico con molti bandi erogati.
                    * **Budget per Azienda (Intensità Economica):** Rappresenta il valore monetario dei contributi ottenuti mediamente da ogni azienda. Confrontare la Mediana Target con la Mediana Totale chiarisce se i fondi nel settore d'interesse (target) sono mediamente più ricchi o più poveri rispetto al mercato generale.
                        * *Esempio:* Se il rapporto tra Mediana Target e Mediana Totale è il **25%**, significa che il finanziamento tipico nel settore target è grande un quarto rispetto a un finanziamento generico. Questo ci dice se il settore target è composto da piccoli contributi o da grandi investimenti.
                    
                    ### 🏢 Indicatori dell'Azienda (Specializzazione)
                    Fattori di FOCALIZZAZIONE (F). Questi valori dipendono dalle scelte strategiche della singola impresa.
                    * **Fattore Fo (Specializzazione Operativa):** Misura la focalizzazione del "fare". È la percentuale di pratiche nel settore target rispetto al totale delle pratiche gestite per un'azienda media. Se è vicina al 100%, l'azienda opera quasi esclusivamente nel target.
                    * **Fattore Fe (Specializzazione Economica):** Misura la focalizzazione del "valore". È la percentuale di budget target rispetto al budget totale incassato. Un valore alto indica che il core-business finanziario dell'azienda è strettamente legato al settore target.
                        * *Esempio:* Se la **Mediana di F2 è il 15%**, significa che metà delle aziende analizzate dedica al settore target meno del 15% del proprio budget totale, mentre l'altra metà di più. 
                        * **Nota bene:** Questo valore indica il comportamento "tipo" delle aziende, ma non ci dice nulla su quanti soldi totali (massa monetaria) ci sono nel sistema.
                    
                    ---
                    💡 **Strategia:** Le aziende sotto mediana rappresentano il segmento con il più alto potenziale di crescita per nuove pianificazioni finanziarie o investimenti mirati.
                    """)
                
            # Creiamo un contenitore con bordo (stile card)
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write("**Numero Aiuti per Azienda**")
                    st.metric("Mediana", f"{med_aiuti:.1f}")
                    st.metric("Mediana Target", f"{med_aiuti_target:.1f}",
                                delta=f"{(med_aiuti_target/med_aiuti)*100:.1f}% del totale", delta_color = "normal")
                    sotto_med_aiuti_target = len(df_benchmark_1[df_benchmark_1['Aiuti Target'] < med_aiuti_target])
                    st.caption(f"📉 {sotto_med_aiuti_target} aziende sotto mediana delle {n_aziende_target} attive nel settore target")
        
                with col2:
                    st.write("**Fattore Fo**")
                    st.write("")
                    st.write("")
                    st.write("")
                    st.metric("Mediana", f"{med_Fo:.1f}%".replace('.', ','))
                    sotto_med_Fo = len(df_benchmark_1[df_benchmark_1['Fo'] < med_Fo])
                    st.caption(f"📉 {sotto_med_Fo} aziende sotto mediana")
        
                with col3:
                    st.write("**Budget per Azienda**")
                    st.metric("Mediana", f"€ {med_budget:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    st.metric("Mediana Target", f"€ {med_budget_target:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                              delta=f"{(med_budget_target/med_budget)*100:.1f}% del totale", delta_color = "normal")
                    # Calcolo aziende sotto la mediana
                    sotto_med_budget_target = len(df_benchmark_1[df_benchmark_1['Budget Target'] < med_budget_target])
                    st.caption(f"📉 {sotto_med_budget_target} aziende sotto mediana delle {n_aziende_target} attive nel settore target")
                    
                with col4:
                    st.write("**Fattore Fe**")
                    st.metric("Mediana", f"{med_Fe:.1f}%".replace('.', ','))
                    # Calcolo aziende sotto la mediana
                    sotto_med_Fe = len(df_benchmark_1[df_benchmark_1['Fe'] < med_Fe])
                    st.caption(f"📉 {sotto_med_Fe} aziende sotto mediana")
                    
        

        # --- SCATTER PLOTS DI POSIZIONAMENTO ---
        # Filtriamo: Budget Target deve essere > 1 per eliminare centesimi o errori di sistema
        df_plot = report_aziende[report_aziende['Budget Target'] > 1].copy()
        if not df_plot.empty:
            st.write("")
            col_graf_1, col_graf_2 = st.columns(2)
            
            # --- GRAFICO 2: POSIZIONAMENTO OPERATIVO (N. Aiuti) ---
            with col_graf_1:
                # Pendenza basata sulla Mediana Fo
                pendenza_Fo = med_Fo / 100
                max_x_aiuti = df_plot["Aiuti"].max()
        
                fig_aiuti_scatter = px.scatter(
                    df_plot,
                    x="Aiuti",
                    y="Aiuti Target",
                    hover_name="Ragione Sociale",
                    color="Fo",
                    title="Specializzazione Operativa (N. Aiuti)",
                    labels={"Aiuti": "Totale Aiuti", "Aiuti Target": "Aiuti Target"},
                    color_continuous_scale="Plasma"
                )
        
                # Linea Mediana Fo
                fig_aiuti_scatter.add_shape(
                    type="line", x0=0, y0=0, x1=max_x_aiuti, y1=max_x_aiuti * pendenza_Fo,
                    line=dict(color="Red", width=2, dash="dash")
                )
        
                fig_aiuti_scatter.update_layout(height=450, showlegend=False)
                st.plotly_chart(fig_aiuti_scatter, use_container_width=True)
                st.caption(f"La linea tratteggiata rappresenta la Mediana Fo ({med_Fo:.1f}%)")
                
            # --- GRAFICO 1: POSIZIONAMENTO ECONOMICO (Budget) ---
            with col_graf_2:
                fig_budget_scatter = px.scatter(
                df_plot,
                x="Budget",
                y="Budget Target",
                log_x=True, 
                log_y=True,
                hover_name="Ragione Sociale",
                color="Fe",
                title="Specializzazione Economica (Scala Log)",
                labels={"Budget": "Totale (€)", "Budget Target": "Target (€)"},
                color_continuous_scale="Viridis"
                )
                # 1. Calcoliamo i limiti del grafico per far attraversare tutto lo spazio alla linea
                x_min = df_plot["Budget"].min()
                x_max = df_plot["Budget"].max()

                # 2. La linea deve seguire l'equazione: y = x * (mediana/100)
                # Su scala logaritmica, questa rimane una retta se disegnata correttamente
                fig_budget_scatter.add_shape(
                    type="line",
                    x0=x_min, 
                    y0=x_min * (med_Fe / 100),
                    x1=x_max, 
                    y1=x_max * (med_Fe / 100),
                    line=dict(color="Red", width=3, dash="dash")
                )

                fig_budget_scatter.update_layout(height=450, showlegend=False)
                st.plotly_chart(fig_budget_scatter, use_container_width=True)
                st.caption(f"La linea tratteggiata rappresenta la Mediana Fe ({med_Fe:.1f}%)")
            
            st.info("""
            **Interpretazione dei quadranti:**
            - **Sopra la linea rossa:** Aziende "Focalizzate" (agiscono sul target più della media dei competitor).
            - **Sotto la linea rossa:** Aziende "Disinteressate" (il target è solo una componente minoritaria della loro attività).
            """)
    
        # --- GRAFICI ---
        df_plot = report_aziende[report_aziende['Budget Target'] > 0].copy()
        if not df_plot.empty:
            with st.expander("📈 Benchmark Visivo"):
                
                # Funzione helper per creare i grafici con lo stesso stile
                def crea_box_orizzontale(df, col, titolo, colore):
                    fig = px.box(
                        df, 
                        x=col, 
                        points="all", 
                        hover_name="Ragione Sociale",
                        title=titolo,
                        color_discrete_sequence=[colore]
                    )
                    # pointpos=0 sovrappone i punti al box
                    # jitter controlla quanto i punti si allargano (0.1 è molto stretto)
                    fig.update_traces(pointpos=0, jitter=0.1, marker=dict(opacity=0.6, size=7))
                    fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
                    return fig
                    
                # GRAFICO: NUMERO AIUTI TARGET
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Aiuti Target", "Distribuzione Numero Aiuti Target", "#9b59b6"),
                    use_container_width=True
                )
                # GRAFICO: Fo
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Fo", "Distribuzione Fattore Fo", "#3498db"),
                    use_container_width=True
                )
                # GRAFICO: BUDGET TARGET
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Budget Target", "Distribuzione Budget Target (€)", "#2ecc71"),
                    use_container_width=True
                )
                # GRAFICO: Fe
                st.plotly_chart(
                    crea_box_orizzontale(df_plot, "Fe", "Distribuzione Fattore Fe", "#e67e22"),
                    use_container_width=True
                )
                
        else:
            st.info("Nessun dato target disponibile per i grafici.")
    
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
