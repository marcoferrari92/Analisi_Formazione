import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    """
    Analisi geografica con auto-rilevamento province, drill-down CAP 
    e tabella analitica con gradiente e dettaglio CAP usati.
    """

    # --- 1. DIZIONARIO DECODIFICA CAP -> PROVINCIA ---
    cap_to_prov = {
        '00': 'Roma', '01': 'Viterbo', '02': 'Rieti', '03': 'Frosinone', '04': 'Latina',
        '05': 'Terni', '06': 'Perugia', '07': 'Sassari', '08': 'Nuoro', '09': 'Cagliari',
        '10': 'Torino', '12': 'Cuneo', '13': 'Vercelli', '14': 'Asti', '15': 'Alessandria',
        '16': 'Genova', '17': 'Savona', '18': 'Imperia', '19': 'La Spezia', '20': 'Milano',
        '21': 'Varese', '22': 'Como', '23': 'Sondrio', '24': 'Bergamo', '25': 'Brescia',
        '26': 'Cremona', '27': 'Pavia', '28': 'Novara', '29': 'Piacenza', '30': 'Venezia',
        '31': 'Treviso', '32': 'Belluno', '33': 'Udine', '34': 'Trieste', '35': 'Padova',
        '36': 'Vicenza', '37': 'Verona', '38': 'Trento', '39': 'Bolzano', '40': 'Bologna',
        '41': 'Modena', '42': 'Reggio Emilia', '43': 'Parma', '44': 'Ferrara', '45': 'Rovigo',
        '46': 'Mantova', '47': 'Forlì-Cesena', '48': 'Ravenna', '50': 'Firenze', '51': 'Pistoia',
        '52': 'Arezzo', '53': 'Siena', '54': 'Massa-Carrara', '55': 'Lucca', '56': 'Pisa',
        '57': 'Livorno', '58': 'Grosseto', '59': 'Prato', '60': 'Ancona', '61': 'Pesaro',
        '62': 'Macerata', '63': 'Ascoli', '64': 'Teramo', '65': 'Pescara', '66': 'Chieti',
        '67': 'L’Aquila', '70': 'Bari', '71': 'Foggia', '72': 'Brindisi', '73': 'Lecce',
        '74': 'Taranto', '75': 'Matera', '80': 'Napoli', '81': 'Caserta', '82': 'Benevento',
        '83': 'Avellino', '84': 'Salerno', '85': 'Potenza', '87': 'Cosenza', '88': 'Catanzaro',
        '89': 'Reggio Calabria', '90': 'Palermo', '91': 'Trapani', '92': 'Agrigento', 
        '93': 'Caltanissetta', '94': 'Enna', '95': 'Catania', '96': 'Siracusa', '97': 'Ragusa', '98': 'Messina'
    }

    # --- 2. PREPARAZIONE DATI ---
    colonna_cap = 'RNA_CAP_BENEFICIARIO' if 'RNA_CAP_BENEFICIARIO' in df.columns else 'CAP'
    
    # Pulizia CAP preventiva per tutto il DF
    df[colonna_cap] = df[colonna_cap].astype(str).str.replace('.0', '', regex=False).str.zfill(5)

    # Aggregazione per Mappe e Tabella
    df_geo_all = df.groupby('RNA_REGIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].agg(['count', 'sum']).reset_index()
    df_geo_all.columns = ['Regione', 'Aiuti_Tot', 'Budget_Tot']

    df_target = df[df['IS_TARGET'] == 1].copy()
    
    # Calcolo lista CAP per ogni regione (per la tabella)
    df_cap_list = df_target.groupby('RNA_REGIONE_BENEFICIARIO')[colonna_cap].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index()
    df_cap_list.columns = ['Regione', 'CAP_Usati']

    df_geo_target = df_target.groupby('RNA_REGIONE_BENEFICIARIO')['RNA_ELEMENTO_DI_AIUTO'].agg(['count', 'sum']).reset_index()
    df_geo_target.columns = ['Regione', 'Aiuti_Targ', 'Budget_Targ']

    # Unione finale Dati
    df_mappe = pd.merge(df_geo_all, df_geo_target, on='Regione', how='left')
    df_mappe = pd.merge(df_mappe, df_cap_list, on='Regione', how='left').fillna(0)
    
    # Mapping GeoJSON
    df_mappe['Regione_Match'] = df_mappe['Regione'].str.strip().str.lower()
    mapping_geo = {
        "friuli-venezia giulia": "friuli venezia giulia",
        "trentino-alto adige": "trentino-alto adige/südtirol",
        "valle d'aosta": "valle d'aosta/vallée d'aoste"
    }
    df_mappe['Regione_Match'] = df_mappe['Regione_Match'].replace(mapping_geo)

    # --- 3. DATI TREEMAP ---
    df_tree_raw = df_target.groupby(['RNA_REGIONE_BENEFICIARIO', colonna_cap])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_tree_raw.columns = ['Regione', 'CAP_Str', 'Budget_Target']
    df_tree_raw['Prov_Key'] = df_tree_raw['CAP_Str'].str[:2]
    df_tree_raw['Provincia'] = df_tree_raw['Prov_Key'].map(cap_to_prov).fillna("Area " + df_tree_raw['Prov_Key'])
    df_tree_raw['CAP_Label'] = "CAP " + df_tree_raw['CAP_Str']

    # --- 4. GEOJSON E STYLE ---
    @st.cache_data
    def get_geojson():
        url = "https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json"
        return requests.get(url).json()
    
    geojson_data = get_geojson()

    def apply_italy_style(fig):
        fig.update_geos(
            visible=True, showland=True, landcolor="#f8f9fa",
            showcoastlines=True, projection_type='mercator',
            lataxis_range=[35, 47.5], lonaxis_range=[6, 19]
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450, coloraxis_colorbar_title_text="")
        return fig

    # --- 5. VISUALIZZAZIONE MAPPE ---
    col_map1, col_map2 = st.columns(2)
    with col_map1:
        fig_tot = px.choropleth(df_mappe, geojson=geojson_data, locations='Regione_Match', 
                                featureidkey="properties.name", color='Budget_Tot', 
                                color_continuous_scale="Blues", title="💰 Mercato Totale (€)",
                                labels={'Budget_Tot': 'Budget'})
        st.plotly_chart(apply_italy_style(fig_tot), use_container_width=True)
    
    with col_map2:
        fig_targ = px.choropleth(df_mappe, geojson=geojson_data, locations='Regione_Match', 
                                 featureidkey="properties.name", color='Budget_Targ', 
                                 color_continuous_scale="Reds", title="🎯 Mercato Target (€)",
                                 labels={'Budget_Targ': 'Budget Target'})
        st.plotly_chart(apply_italy_style(fig_targ), use_container_width=True)

    # --- 6. TREEMAP ---
    st.write("### 🔍 Drill-down Geografico")
    fig_tree = px.treemap(
        df_tree_raw, 
        path=[px.Constant("Italia"), 'Regione', 'Provincia', 'CAP_Label'],
        values='Budget_Target', color='Budget_Target', color_continuous_scale='Reds',
        labels={'Budget_Target': 'Budget', 'CAP_Label': 'CAP'},
        hover_data={'Budget_Target': ':,.0f'}
    )
    fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=600)
    st.plotly_chart(fig_tree, use_container_width=True)

    # --- 7. TABELLA ANALITICA CON GRADIENTE E MATCH ---
    st.write("### 📊 Riepilogo Regionale Dettagliato")
    
    # Preparazione colonne per la tabella
    df_tab = df_mappe[[
        'Regione', 'Regione_Match', 'Aiuti_Tot', 'Aiuti_Targ', 
        'Budget_Tot', 'Budget_Targ', 'CAP_Usati'
    ]].sort_values(by='Budget_Targ', ascending=False)
    
    # Rinominiamo per l'utente finale
    df_tab.columns = ['Regione', 'Match Key', 'Aiuti Tot', 'Aiuti Target', 'Budget Totale', 'Budget Target', 'Lista CAP Target']
    
    # Rendering con background_gradient (Richiede Matplotlib)
    st.dataframe(
        df_tab.style.background_gradient(cmap='Reds', subset=['Budget Target']),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget Totale": st.column_config.NumberColumn(format="€ %,.0f"),
            "Budget Target": st.column_config.NumberColumn(format="€ %,.0f"),
            "Match Key": st.column_config.TextColumn(help="Nome tecnico usato per il GeoJSON"),
            "Lista CAP Target": st.column_config.TextColumn(width="medium", help="CAP rilevati nel settore target")
        }
    )
