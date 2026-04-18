import streamlit as st
import pandas as pd
import io
import plotly.express as px
import json
import requests


# Caricamenti
from settings import DEFAULT_KEYWORDS, GUIDA_BENCHMARK
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

        

        # --- ANALISI GEOGRAFICA ---
        with st.expander("🗺️ Distribuzione Geografica Budget Target"):

            # Verifichiamo la colonna nel tuo file (RNA_REGIONE_BENEFICIARIO)
            col_regione = 'RNA_REGIONE_BENEFICIARIO'

            if col_regione in df.columns:
                # 1. Preparazione Dati: sommiamo il budget target per regione
                df_geo = df[df['IMPORTO_TARGET'] > 0].groupby(col_regione).agg({
                    'IMPORTO_TARGET': 'sum',
                    'RNA_CODICE_FISCALE_BENEFICIARIO': 'nunique'
                }).reset_index()
    
                df_geo.columns = ['Regione', 'Budget_Target', 'N_Aziende']
    
                # Pulizia nomi (per matchare il GeoJSON)
                # Es. "Valle d'Aosta/Vallée d'Aoste" -> "Valle d'Aosta"
                df_geo['Regione'] = df_geo['Regione'].str.split('/').str[0].str.strip()

                # Creazione delle due colonne per i grafici
                g1, g2 = st.columns([1, 1.2])

                with g1:
                    # --- TREEMAP ---
                    # Poiché non abbiamo la provincia, usiamo Regione e opzionalmente 
                    # possiamo aggiungere il settore o lo strumento come sottolivello
                    fig_tree = px.treemap(
                        df_geo,
                        path=[px.Constant("Italia"), 'Regione'],
                        values='Budget_Target',
                        color='Budget_Target',
                        color_continuous_scale='Viridis',
                        hover_data=['N_Aziende'],
                        title="Peso Economico per Regione"
                    )
                    fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10))
                    st.plotly_chart(fig_tree, use_container_width=True)
                    st.caption("La dimensione dei rettangoli indica il volume economico erogato nel target.")

                with g2:
                    # 1. Scarichiamo il GeoJSON (URL di Stefano Cudini che hai testato)
                    geojson_url = "https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json"
                    try:
                        resp = requests.get(geojson_url)
                        geojson_data = resp.json()
                
                        # 2. Normalizzazione CRITICA per questo file:
                        # Il file vuole i nomi TUTTI MINUSCOLI (piemonte, lazio, veneto...)
                        df_geo['Regione_Match'] = df_geo['Regione'].str.strip().str.lower()
                        
                        # Correzione nomi composti per matchare il file di Cudini
                        mapping_speciali = {
                            "friuli-venezia giulia": "friuli venezia giulia", # Tolto il trattino
                            "trentino-alto adige": "trentino-alto adige/südtirol",
                            "valle d'aosta": "valle d'aosta/vallée d'aoste"
                        }
                        df_geo['Regione_Match'] = df_geo['Regione_Match'].replace(mapping_speciali)
                
                        # 3. Creazione Mappa
                        fig_map = px.choropleth(
                            df_geo,
                            geojson=geojson_data,
                            locations='Regione_Match',
                            featureidkey="properties.name",
                            color='Budget_Target',
                            color_continuous_scale="Reds",
                            title="Distribuzione Regionale Budget Target"
                        )
                    
                        # 4. Modifica per vedere tutta l'Italia
                        fig_map.update_geos(
                            visible=True,           # Rende visibili i confini geografici di base
                            resolution=50,          # Dettaglio della mappa
                            showcountries=True,
                            showcoastlines=True,
                            projection_type='mercator',
                            # Impostiamo manualmente le coordinate per centrare l'Italia
                            lataxis_range=[35, 47.5], 
                            lonaxis_range=[6, 19]
                        )
                        
                        # Rimuoviamo fitbounds="locations" (è lui che "taglia" la mappa)
                        # fig_map.update_geos(fitbounds="locations") <--- ELIMINA O COMMENTA QUESTA RIGA
                    
                        fig_map.update_layout(
                            margin={"r":0,"t":40,"l":0,"b":0}, 
                            height=500,
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                    
                        st.plotly_chart(fig_map, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Errore tecnico nella mappa: {e}")
                
                    # DEBUG FINALE (se ancora non vedi colore, guarda questa tabella sotto il grafico)
                    # st.write("Verifica Match:", df_geo[['Regione', 'Regione_Match']])
            else:
                st.error(f"Colonna '{col_regione}' non trovata nel file CSV.")
        
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
                st.markdown(GUIDA_BENCHMARK)
                
            # Creiamo un contenitore con bordo (stile card)
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write("**Numero Aiuti per Azienda**")
                    st.metric("Mediana Totale", f"{med_aiuti:.1f}")
                    st.metric("Mediana Target", f"{med_aiuti_target:.1f}",
                                delta=f"{(med_aiuti_target/med_aiuti)*100:.1f}% del totale", delta_color = "normal")
                    sotto_med_aiuti_target = len(df_benchmark_1[df_benchmark_1['Aiuti Target'] < med_aiuti_target])
                    st.caption(f"📉 {sotto_med_aiuti_target} aziende sotto mediana delle {n_aziende_target} attive nel settore target")
        
                with col2:
                    st.write("**Budget per Azienda**")
                    st.metric("Mediana Totale", f"€ {med_budget:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    st.metric("Mediana Target", f"€ {med_budget_target:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                              delta=f"{(med_budget_target/med_budget)*100:.1f}% del totale", delta_color = "normal")
                    # Calcolo aziende sotto la mediana
                    sotto_med_budget_target = len(df_benchmark_1[df_benchmark_1['Budget Target'] < med_budget_target])
                    st.caption(f"📉 {sotto_med_budget_target} aziende sotto mediana delle {n_aziende_target} attive nel settore target")
        
                with col3:
                    st.write("**Fattore Fo**")
                    st.metric("Mediana", f"{med_Fo:.1f}%".replace('.', ','))
                    sotto_med_Fo = len(df_benchmark_1[df_benchmark_1['Fo'] < med_Fo])
                    st.caption(f"📉 {sotto_med_Fo} aziende sotto mediana")
                    
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
            with st.expander("📈 Analisi Outliers"):
                
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
        st.write("")
        
        if search_txt:
            # Filtro per Ragione Sociale
            azienda_details = df[df['RAGIONE SOCIALE'].str.contains(search_txt, case=False, na=False)].copy()
            azienda_stats = report_aziende[report_aziende['Ragione Sociale'].str.contains(search_txt, case=False, na=False)]
            
            if not azienda_stats.empty:
                # Prendiamo la prima occorrenza (in caso di nomi simili)
                row = azienda_stats.iloc[0]
        
                st.markdown(f"#### 📊 Performance vs Benchmark: **{row['Ragione Sociale']}**")
        
                # Creiamo 4 colonne per il confronto diretto
                b1, b2, b3, b4 = st.columns(4)
        
                with b1:
                    diff_aiuti = row['Aiuti Target'] - med_aiuti_target
                    st.metric("Aiuti Target", f"{row['Aiuti Target']}", 
                      delta=f"{diff_aiuti:+.1f} vs mediana", 
                      delta_color="normal")
            
                with b2:
                    diff_budget = row['Budget Target'] - med_budget_target
                    st.metric("Budget Target", f"€ {row['Budget Target']:,.0f}".replace(',', '.'), 
                      delta=f"€ {diff_budget:+.0f}".replace(',', '.'), 
                      delta_color="normal")
            
                with b3:
                    diff_fo = row['Fo'] - med_Fo
                    st.metric("Fattore Fo", f"{row['Fo']:.1f}%", 
                      delta=f"{diff_fo:+.1f}% vs mediana")
            
                with b4:
                    diff_fe = row['Fe'] - med_Fe
                    st.metric("Fattore Fe", f"{row['Fe']:.1f}%", 
                      delta=f"{diff_fe:+.1f}% vs mediana")
        
                st.divider()
                
            if not azienda_details.empty:
                # 1. Mapping di sicurezza (se i nomi nel DF sono diversi da quelli desiderati per la tabella)
                # Assicuriamoci che le colonne esistano prima di rinominare o usare
                map_colonne = {
                    'RNA_DATA_CONCESSIONE': 'RNA_DATA',
                    'RNA_TITOLO_MISURA': 'RNA_MISURA',
                    'RNA_ELEMENTO_DI_AIUTO': 'RNA_IMPORTO',
                    'IS_TARGET': 'is_target'
                }
        
                # Rinominiamo solo quelle presenti per evitare errori
                azienda_details = azienda_details.rename(columns={k: v for k, v in map_colonne.items() if k in azienda_details.columns})

                # 2. Definizione Ordine
                colonne_prioritarie = [
                    'RNA_DATA', 'RNA_CAR', 'RNA_MISURA', 'RNA_TITOLO_PROGETTO', 
                    'RNA_IMPORTO', 'is_target', 'RAGIONE SOCIALE', 'CF_TROVATO'
                ]
        
                # Filtriamo solo quelle che esistono davvero dopo il rinnovo
                ordine_esistente = [c for c in colonne_prioritarie if c in azienda_details.columns]
                altre_col_rna = [c for c in azienda_details.columns if c.startswith('RNA_') and c not in ordine_esistente]
                ordine_finale = ordine_esistente + altre_col_rna

                st.write(f"### Dettaglio estrazione: {azienda_details['RAGIONE SOCIALE'].iloc[0]}")
        
                # Visualizzazione Tabella con stile
                st.dataframe(
                    azienda_details[ordine_finale].style.apply(
                        lambda r: ['background-color: #d4edda' if r.get('is_target', 0) == 1 else ''] * len(r), axis=1
                    ),
                    column_config={
                        "RNA_DATA": st.column_config.DateColumn("📅 Data", format="DD/MM/YYYY"),
                        "RNA_CAR": st.column_config.TextColumn("CAR"),
                        "RNA_MISURA": st.column_config.TextColumn("📜 Titolo Misura", width="large"),
                        "RNA_TITOLO_PROGETTO": st.column_config.TextColumn("🏗️ Titolo Progetto", width="medium"),
                        "RNA_IMPORTO": st.column_config.NumberColumn("💰 Aiuto (€)", format="€ %.2f"),
                        "is_target": st.column_config.CheckboxColumn("🎯 Target"),
                        "RNA_LINK_TRASPARENZA_NAZIONALE": st.column_config.LinkColumn("🔗 Link Trasparenza"),
                        "RNA_LINK_TESTO_INTEGRALE_MISURA": st.column_config.LinkColumn("📄 Bando"),
                    },
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning(f"Nessuna azienda trovata per: {search_txt}")

        
        try:
            # Verifichiamo quale DataFrame usare per il download
            df_da_scaricare = report_aziende if 'report_aziende' in locals() else df
    
            csv_buffer = io.BytesIO()
            df_da_scaricare.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
            st.sidebar.download_button(
                label="💾 Scarica Report (CSV)",
                data=csv_buffer.getvalue(),
                file_name="Report_RNA.csv",
                mime="text/csv"
            )
        except NameError:
            st.sidebar.error("⚠️ Errore: DataFrame per il download non trovato.")

    except Exception as e:
        st.error(f"Errore generale nell'applicazione: {e}")

else:
    st.info("👋 Carica il file per iniziare.")
