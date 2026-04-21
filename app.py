import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import json
import requests


# Caricamenti
from settings import DEFAULT_KEYWORDS, GUIDA_BENCHMARK, GUIDA_PARETO, GUIDA_RICERCA
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
keywords_raw = st.sidebar.text_area("Parole chiave target", value=DEFAULT_KEYWORDS)
with st.sidebar.popover("ℹ️ Info logica di ricerca"):
    st.markdown(GUIDA_RICERCA)

st.sidebar.header("3. Range Temporale")
data_range = None



# ANALISI
if uploaded_file is not None:
    try:

        # Caricamento dei dati integrale
        df_raw = load_rna_data(uploaded_file)

        # --- FILTRO TEMPORALE  ---
        
        # Convertiamo la colonna data in datetime per poter calcolare i limiti
        df_raw['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_raw['RNA_DATA_CONCESSIONE'], errors='coerce')
        min_date_file = df_raw['RNA_DATA_CONCESSIONE'].min().date() if not df_raw['RNA_DATA_CONCESSIONE'].dropna().empty else None
        max_date_file = df_raw['RNA_DATA_CONCESSIONE'].max().date() if not df_raw['RNA_DATA_CONCESSIONE'].dropna().empty else None

        if min_date_file and max_date_file:
            data_range = st.sidebar.date_input(
                "Seleziona periodo di analisi",
                value=(min_date_file, max_date_file),
                min_value=min_date_file,
                max_value=max_date_file
            )
            
            # Applichiamo il filtro se l'utente ha selezionato un range completo (inizio e fine)
            if len(data_range) == 2:
                start_date, end_date = data_range
                df = df_raw[
                    (df_raw['RNA_DATA_CONCESSIONE'].dt.date >= start_date) & 
                    (df_raw['RNA_DATA_CONCESSIONE'].dt.date <= end_date)
                ].copy()
            else:
                df = df_raw.copy()
        else:
            df = df_raw.copy()
            st.sidebar.warning("⚠️ Nessuna data valida trovata nel file.")

        btn_ricerca = st.sidebar.button("🔍 Aggiorna Analisi", use_container_width=True, type="primary")
        
        # RICERCA TARGETS NEL DATAFRAME (e relativi importi)
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
            # Budget Totale
            st.metric(label="Budget Totale", value=f"€ {budget_totale:,.0f}")
            
            # Budget Target
            st.metric(label="Budget Target",value=f"€ {budget_target:,.0f}",delta=f"{perc_budget_target:.1f}% del budget totale")

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
        st.write("")
        st.write("")
        with st.expander("🗺️ Distribuzione Geografica Settore Target"):
            
            st.write("")
            # 1. Preparazione Dati
            df_geo_all = df.groupby('RNA_REGIONE_BENEFICIARIO').agg({'RNA_TITOLO_MISURA': 'count', 'RNA_ELEMENTO_DI_AIUTO': 'sum'}).reset_index()
            df_geo_target = df[df['IS_TARGET'] == 1].groupby('RNA_REGIONE_BENEFICIARIO').agg({'RNA_TITOLO_MISURA': 'count', 'RNA_ELEMENTO_DI_AIUTO': 'sum'}).reset_index()
            
            df_mappe = pd.merge(df_geo_all, df_geo_target, on='RNA_REGIONE_BENEFICIARIO', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
            df_mappe['Regione_Match'] = df_mappe['RNA_REGIONE_BENEFICIARIO'].str.strip().str.lower()
            
            # Mapping per matchare il GeoJSON di Cudini
            mapping_geo = {
                "friuli-venezia giulia": "friuli venezia giulia",
                "trentino-alto adige": "trentino-alto adige/südtirol",
                "valle d'aosta": "valle d'aosta/vallée d'aoste"
            }
            df_mappe['Regione_Match'] = df_mappe['Regione_Match'].replace(mapping_geo)
            
            # Scarico GeoJSON
            geojson_url = "https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json"
            geojson_data = requests.get(geojson_url).json()
            
            # Funzione per lo stile "Tutta Italia"
            def apply_italy_full_style(fig):
                fig.update_geos(
                    visible=True,           # Mostra lo sfondo
                    showland=True,          # Mostra la terraferma
                    landcolor="#f8f9fa",    # Colore neutro per regioni senza dati
                    showcoastlines=True, 
                    projection_type='mercator',
                    lataxis_range=[35, 47.5], 
                    lonaxis_range=[6, 19]
                )
                fig.update_layout(
                    margin={"r":0,"t":40,"l":0,"b":0}, 
                    height=450,
                    coloraxis_showscale=True,
                    coloraxis_colorbar_title_text=""
                )
                return fig
            
            # --- LAYOUT COLONNE ---
            col_map1, col_map2 = st.columns(2)
            
            with col_map1:
                fig_tot = px.choropleth(
                    df_mappe, geojson=geojson_data, locations='Regione_Match', featureidkey="properties.name",
                    color='RNA_ELEMENTO_DI_AIUTO_Tot', 
                    color_continuous_scale="Blues", # Scala Blu per il generale
                    title="💰 Mercato Totale"
                )
                fig_tot.update_layout(title_x=0.25) 
                st.plotly_chart(apply_italy_full_style(fig_tot), use_container_width=True)
            
            with col_map2:
                fig_targ = px.choropleth(
                    df_mappe, geojson=geojson_data, locations='Regione_Match', featureidkey="properties.name",
                    color='RNA_ELEMENTO_DI_AIUTO_Targ', 
                    color_continuous_scale="Reds", # Scala Rossa per il target
                    title="🎯 Mercato Target"
                )
                fig_targ.update_layout(title_x=0.25)
                st.plotly_chart(apply_italy_full_style(fig_targ), use_container_width=True)
                st.write("")
            
            # --- TREEMAP ORIZZONTALE SOTTO ---         
            # Mostriamo solo le regioni che hanno effettivamente dati target
            df_tree = df_mappe[df_mappe['RNA_ELEMENTO_DI_AIUTO_Targ'] > 0]
            fig_tree = px.treemap(
                df_tree, 
                path=[px.Constant("Italia"), 'RNA_REGIONE_BENEFICIARIO'],
                values='RNA_ELEMENTO_DI_AIUTO_Targ', 
                color='RNA_ELEMENTO_DI_AIUTO_Targ',
                color_continuous_scale='Reds',
                title="Distribuzione Gerarchica del Budget Target",
                hover_data={'RNA_ELEMENTO_DI_AIUTO_Targ': ':,.0f'}
                )

            # 2. Centra il titolo e regola i margini
            fig_tree.update_layout(
                title_x=0.5, 
                margin=dict(t=50, l=10, r=10, b=10), # Aumentato il margine superiore (t) per far spazio al titolo
                height=400,
                coloraxis_colorbar_title_text=""
            )
            st.plotly_chart(fig_tree, use_container_width=True)
                
            # --- TABELLA ---
            # 1. Calcolo i totali per Regione (Mercato Generale)
            df_reg_tot = df.groupby('RNA_REGIONE_BENEFICIARIO').agg({
                'RNA_TITOLO_MISURA': 'count',
                'RNA_ELEMENTO_DI_AIUTO': 'sum'
            }).reset_index()
            
            # 2. Calcolo i totali per Regione (Solo Target)
            df_reg_targ = df[df['IS_TARGET'] == 1].groupby('RNA_REGIONE_BENEFICIARIO').agg({
                'RNA_TITOLO_MISURA': 'count',
                'RNA_ELEMENTO_DI_AIUTO': 'sum'
            }).reset_index()
            
            # 3. Unione e pulizia
            df_reg_tabella = pd.merge(
                df_reg_tot, 
                df_reg_targ, 
                on='RNA_REGIONE_BENEFICIARIO', 
                how='left'
            ).fillna(0)
            
            # 4. Rinomina e Ordine Colonne richiesto
            df_reg_tabella.columns = ['Regione', 'Aiuti', 'Budget', 'Aiuti Target', 'Budget Target']
            ordine_richiesto = ['Regione', 'Aiuti', 'Aiuti Target', 'Budget', 'Budget Target']
            df_reg_tabella = df_reg_tabella[ordine_richiesto]
            
            # 5. Ordinamento per importanza economica
            df_reg_tabella = df_reg_tabella.sort_values(by='Budget Target', ascending=False)
            
            # --- VISUALIZZAZIONE STREAMLIT ---
            st.write("")
            st.dataframe(
                df_reg_tabella,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Regione": st.column_config.TextColumn("Regione"),
                    "Aiuti": st.column_config.NumberColumn("Aiuti", format="%d"),
                    "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d"),
                    "Budget": st.column_config.NumberColumn(
                        "Budget (€)", 
                        format="€ %,.0f"
                    ),
                    "Budget Target": st.column_config.NumberColumn(
                        "Budget Target (€)", 
                        format="€ %,.0f"
                    ),
                }
            )
        st.write("")
        st.write("")



        # --- SEZIONE TEMPORALE DENTRO EXPANDER ---
        with st.expander("📅 Distribuzione Temporale Settore Target"):
            
            # 1. Preparazione Dati
            # Assicurati che la data sia in formato datetime
            df['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df['RNA_DATA_CONCESSIONE'])
            
            # Creiamo le colonne di supporto per l'aggregazione
            df['AnnoMonth'] = df['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
            df['Anno'] = df['RNA_DATA_CONCESSIONE'].dt.year
            df['Mese_Num'] = df['RNA_DATA_CONCESSIONE'].dt.month
            
            # --- GRAFICO A AREA (ANDAMENTO MENSILE) ---
            st.subheader("📈 Evoluzione del Budget nel Tempo")
            
            # Aggreghiamo Totale e Target
            df_time_tot = df.groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
            df_time_targ = df[df['IS_TARGET'] == 1].groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
            
            df_time_plot = pd.merge(df_time_tot, df_time_targ, on='AnnoMonth', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
            df_time_plot.columns = ['Periodo', 'Mercato Totale', 'Settore Target']

            df_time_plot['Quota Target (%)'] = (df_time_plot['Settore Target'] / df_time_plot['Mercato Totale'] * 100).fillna(0)
            
            # --- 1. GRAFICO INCIDENZA % (Sopra) ---
            fig_norm = px.area(
                df_time_plot, x='Periodo', y='Quota Target (%)',
                title="Quota di Mercato del Settore Target",
                template="plotly_white", line_shape="spline", markers=True
            )
            fig_norm.update_traces(line_color='#e74c3c', fill='tozeroy')
            fig_norm.update_layout(
                yaxis_ticksuffix="%", 
                margin=dict(l=60, r=20, t=50, b=0), # Margini fissi per allineamento
                height=350
            )
            
            # --- 2. GRAFICO VALORI ASSOLUTI (Sotto) ---
            fig_line = px.line(
                df_time_plot, x='Periodo', y=['Mercato Totale', 'Settore Target'],
                color_discrete_map={"Mercato Totale": "#3498db", "Settore Target": "#e74c3c"},
                title="Evoluzione Temporale del Mercato",
                template="plotly_white", line_shape="spline"
            )
            
            fig_line.update_layout(
                # SPOSTAMENTO LEGENDA: la mettiamo in alto orizzontale
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="right", 
                    x=1
                ),
                # ALLINEAMENTO MARGINI: l=60 deve essere uguale al grafico sopra
                margin=dict(l=60, r=20, t=50, b=50), 
                height=350,
                xaxis_title="Periodo",
                yaxis_title="Budget (€)"
            )
            
            # Visualizzazione con chiavi univoche per evitare conflitti di ID
            st.plotly_chart(fig_norm, use_container_width=True, key="grafico_incidenza_percentuale")
            st.plotly_chart(fig_line, use_container_width=True, key="grafico_budget_assoluto")

            st.divider()
        
            # --- HEATMAP (STAGIONALITÀ) ---
            st.subheader("🔥 Intensità delle Concessioni per Mese e Anno")
      
            df_heat_data = df[df['IS_TARGET'] == 1].groupby(['Anno', 'Mese_Num'])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
            df_heat_data = df_heat_data.sort_values(by='Anno', ascending=False)
            pivot_heat = df_heat_data.pivot(index='Anno', columns='Mese_Num', values='RNA_ELEMENTO_DI_AIUTO').fillna(0)
            pivot_heat = pivot_heat.sort_index(ascending=False)
            
            # Mapping nomi mesi (rimane uguale)
            mesi_ita = {1:'Gen', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mag', 6:'Giu', 7:'Lug', 8:'Ago', 9:'Set', 10:'Ott', 11:'Nov', 12:'Dic'}
            pivot_heat.columns = [mesi_ita.get(c, c) for c in pivot_heat.columns]
            
            # --- GRAFICO ---
            fig_heat = px.imshow(
                pivot_heat,
                labels=dict(x="Mese", y="Anno", color="Budget (€)"),
                x=pivot_heat.columns,
                y=[str(a) for a in pivot_heat.index], # Trasformiamo gli anni in stringhe per l'asse categorico
                color_continuous_scale="Reds",
                text_auto=".2s"
            )
            
            fig_heat.update_layout(
                coloraxis_colorbar_title_text="",
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(
                    type='category', 
                    autorange="reversed" # Ora che i dati sono già ordinati nel DF, lasciamo True
                )
            )
            
            st.plotly_chart(fig_heat, use_container_width=True)
            
            st.info("💡 **Consiglio Commerciale:** I mesi con i quadrati più scuri indicano quando le aziende ricevono liquidità. È il momento migliore per proporre nuovi investimenti.")
        st.write("")
        st.write("")



        
        # --- SEZIONE RANKING E ANALISI PARETO ---
        with st.expander("🏆 Ranking Beneficiari e Analisi di Mercato (Pareto)"):
        
            # 1. Preparazione Dati: Top 10 Beneficiari
            df_top_10 = df[df['IS_TARGET'] == 1].groupby('RNA_DENOMINAZIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
            df_top_10 = df_top_10.sort_values(by='RNA_ELEMENTO_DI_AIUTO', ascending=False).head(10)
        
            # --- BAR CHART ORIZZONTALE (TOP 10) ---
            st.subheader("🔝 Top 10 Player del Settore Target")
            
            fig_top = px.bar(
                df_top_10,
                x='RNA_ELEMENTO_DI_AIUTO',
                y='RNA_DENOMINAZIONE_BENEFICIARIO',
                orientation='h',
                text_auto='.2s',
                color='RNA_ELEMENTO_DI_AIUTO',
                color_continuous_scale='Reds',
                labels={'RNA_ELEMENTO_DI_AIUTO': 'Budget Target Totale (€)', 'RNA_DENOMINAZIONE_BENEFICIARIO': 'Azienda'}
            )
            
            fig_top.update_layout(
                yaxis={'categoryorder': 'total ascending'}, 
                coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=30, b=0),
                height=450
            )
            st.plotly_chart(fig_top, use_container_width=True, key="bar_top_10")
        
            st.divider()
        
            # --- ANALISI DI PARETO (80/20) CON INTERSEZIONE ---
            st.subheader("📉 Analisi di Concentrazione (Curva di Pareto)")
            with st.expander("📖 Guida alla lettura e Metodologia"):
                st.markdown(GUIDA_PARETO)
                
            # 1. Preparazione dati (già ordinati per budget decrescente)
            df_pareto = df[df['IS_TARGET'] == 1].groupby('RNA_DENOMINAZIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
            df_pareto = df_pareto.sort_values(by='RNA_ELEMENTO_DI_AIUTO', ascending=False)
            
            df_pareto['Cumsum'] = df_pareto['RNA_ELEMENTO_DI_AIUTO'].cumsum()
            total_budget = df_pareto['RNA_ELEMENTO_DI_AIUTO'].sum()
            df_pareto['Percentage'] = (df_pareto['Cumsum'] / total_budget) * 100
            df_pareto['N_Aziende_Count'] = range(1, len(df_pareto) + 1)
            
            # 2. Trova il punto di intersezione per l'80%
            # Cerchiamo la prima azienda che fa superare la soglia dell'80%
            intersezione = df_pareto[df_pareto['Percentage'] >= 80].iloc[0]
            x_intersezione = intersezione['N_Aziende_Count']
                      
            fig_pareto = go.Figure()
            
            # Barre: Budget per singola azienda
            fig_pareto.add_trace(go.Bar(
                x=df_pareto['N_Aziende_Count'],
                y=df_pareto['RNA_ELEMENTO_DI_AIUTO'],
                name="Budget Azienda",
                marker_color='#3498db',
                opacity=0.4
            ))
            
            # Linea: Percentuale cumulata
            fig_pareto.add_trace(go.Scatter(
                x=df_pareto['N_Aziende_Count'],
                y=df_pareto['Percentage'],
                name="% Cumulata Budget",
                line=dict(color='#e74c3c', width=3),
                yaxis="y2"
            ))
            
            # --- AGGIUNTA RETTE DI INTERSEZIONE ---
            
            # Retta Orizzontale (Soglia 80%)
            fig_pareto.add_hline(
                y=80, yref="y2", 
                line_dash="dash", line_color="gray", 
                annotation_text="Soglia 80%", annotation_position="top left"
            )
            
            # Retta Verticale (Punto di caduta su Asse X)
            fig_pareto.add_vline(
                x=x_intersezione, 
                line_dash="dot", line_color="black", line_width=2,
                annotation_text=f" {int(x_intersezione)} Aziende", 
                annotation_position="top right"
            )
            
            # Punto di intersezione (opzionale, per evidenziare il nodo)
            fig_pareto.add_trace(go.Scatter(
                x=[x_intersezione], y=[80],
                mode='markers',
                marker=dict(color='black', size=10, symbol='circle'),
                yaxis="y2",
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig_pareto.update_layout(
                xaxis_title="Numero di Aziende (Ordinate per Budget Target)",
                yaxis_title="Budget Target della Singola Azienda (€)",
                yaxis2=dict(title="% Cumulata", overlaying="y", side="right", range=[0, 105], ticksuffix="%"),
                legend=dict(orientation="h", y=1.15),
                margin=dict(l=0, r=0, t=60, b=0),
                height=550
            )
            
            st.plotly_chart(fig_pareto, use_container_width=True, key="pareto_intersezione")
        st.write("")
        st.write("")



        
        # --- SEZIONE ANALISI BANDI E MISURE ---
        with st.expander("📜 Analisi dei Bandi e delle Misure (Opportunità)"):
        
            # 1. Definizione della colonna corretta identificata nel CSV
            col_misura = 'RNA_TITOLO_MISURA' 
            
            # Raggruppamento per bando
            df_bandi = df[df['IS_TARGET'] == 1].groupby(col_misura)['RNA_ELEMENTO_DI_AIUTO'].agg(['sum', 'count']).reset_index()
            df_bandi.columns = ['Misura', 'Budget_Totale', 'Numero_Concessioni']
            
            # Ordiniamo per budget e prendiamo i primi 10
            df_bandi_top = df_bandi.sort_values(by='Budget_Totale', ascending=False).head(10)
        
            # --- BAR CHART ORIZZONTALE (TOP BANDI) ---
            st.subheader("💰 I 10 Bandi più generosi per il Settore Target")
            
            fig_bandi = px.bar(
                df_bandi_top,
                x='Budget_Totale',
                y='Misura',
                orientation='h',
                text_auto='.2s',
                color='Budget_Totale',
                color_continuous_scale='Reds',
                hover_data={'Numero_Concessioni': True, 'Budget_Totale': ':,.2f'},
                labels={'Budget_Totale': 'Budget Erogato (€)', 'Misura': 'Nome del Bando/Misura'}
            )
            
            fig_bandi.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=30, b=0),
                height=500
            )
            st.plotly_chart(fig_bandi, use_container_width=True, key="bar_top_bandi_success")
        
            # --- INSIGHTS SUI BANDI ---
            if not df_bandi_top.empty:
                top_bando_nome = df_bandi_top.iloc[0]['Misura']
                budget_target_tot = df[df['IS_TARGET'] == 1]['RNA_ELEMENTO_DI_AIUTO'].sum()
                top_bando_peso = (df_bandi_top.iloc[0]['Budget_Totale'] / budget_target_tot) * 100
        
        
            st.divider()
        
            # 2. Analisi "Taglio Medio"
            st.subheader("📊 Analisi del 'Ticket Medio' per Bando")
            
            df_bandi_top['Ticket_Medio'] = df_bandi_top['Budget_Totale'] / df_bandi_top['Numero_Concessioni']
            
            fig_ticket = px.scatter(
                df_bandi_top,
                x='Numero_Concessioni',
                y='Ticket_Medio',
                size='Budget_Totale',
                color='Misura',
                hover_name='Misura',
                title="Volume Concessioni vs Valore Medio per Bando",
                labels={'Ticket_Medio': 'Importo Medio per Azienda (€)', 'Numero_Concessioni': 'N. Aziende Agevolate'}
            )
            
            fig_ticket.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_ticket, use_container_width=True, key="scatter_ticket_medio_success")



    
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

        # --- 5. TABELLA ---
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
                "Budget": st.column_config.NumberColumn(
                    "Budget Totale (€)",
                    format="€ %,.2f"),
                "Budget Target": st.column_config.NumberColumn(
                    "Budget Target (€)",
                    format="€ %,.2f"),
                "Fo": st.column_config.NumberColumn(
                    "Fo (%)",
                    format="%.1f%%",
                    help="Incidenza numero aiuti target"),
                "Fe": st.column_config.NumberColumn(
                    "Fe (%)",
                    format="%.1f%%",
                    help="Incidenza budget target")
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
                    # 1. Calcolo numerico
                    diff_budget = float(row['Budget Target'] - med_budget_target)
                    
                    # 2. Formattazione Valore Principale (Punto per migliaia)
                    valore_mostrato = f"€ {row['Budget Target']:,.0f}".replace(',', '.')
                    
                    # 3. Formattazione Delta: 
                    # Usiamo il trucco di mettere il segno meno all'inizio se il numero è negativo
                    if diff_budget >= 0:
                        delta_mostrato = f"+€ {diff_budget:,.0f}".replace(',', '.')
                    else:
                        # Rimuoviamo il segno meno automatico per gestirlo manualmente prima dell'Euro
                        delta_mostrato = f"-€ {abs(diff_budget):,.0f}".replace(',', '.')
                    
                    st.metric(
                        label="Budget Target", 
                        value=valore_mostrato, 
                        delta=delta_mostrato,
                        delta_color="normal"
                    )
            
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
