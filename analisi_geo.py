import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    """
    Analisi geografica con Intelligence CAP: ricostruisce Regione e Provincia
    basandosi sul codice postale per correggere errori nel file di input.
    """

    # --- 1. DATABASE DI INTELLIGENCE GEOGRAFICA (CAP -> PROVINCIA, REGIONE) ---
    # Nota: Ho usato le virgolette doppie "" per evitare conflitti con gli apostrofi (es. L'Aquila)
    geo_db = {
        "00": ("Roma", "Lazio"), "01": ("Viterbo", "Lazio"), "02": ("Rieti", "Lazio"),
        "03": ("Frosinone", "Lazio"), "04": ("Latina", "Lazio"), "05": ("Terni", "Umbria"),
        "06": ("Perugia", "Umbria"), "07": ("Sassari", "Sardegna"), "08": ("Nuoro", "Sardegna"),
        "09": ("Cagliari", "Sardegna"), "10": ("Torino", "Piemonte"), "11": ("Aosta", "Valle d'Aosta"),
        "12": ("Cuneo", "Piemonte"), "13": ("Vercelli", "Piemonte"), "14": ("Asti", "Piemonte"),
        "15": ("Alessandria", "Piemonte"), "16": ("Genova", "Liguria"), "17": ("Savona", "Liguria"),
        "18": ("Imperia", "Liguria"), "19": ("La Spezia", "Liguria"), "20": ("Milano", "Lombardia"),
        "21": ("Varese", "Lombardia"), "22": ("Como", "Lombardia"), "23": ("Sondrio", "Lombardia"),
        "24": ("Bergamo", "Lombardia"), "25": ("Brescia", "Lombardia"), "26": ("Cremona", "Lombardia"),
        "27": ("Pavia", "Lombardia"), "28": ("Novara", "Piemonte"), "29": ("Piacenza", "Emilia-Romagna"),
        "30": ("Venezia", "Veneto"), "31": ("Treviso", "Veneto"), "32": ("Belluno", "Veneto"),
        "33": ("Udine", "Friuli-Venezia Giulia"), "34": ("Trieste", "Friuli-Venezia Giulia"),
        "35": ("Padova", "Veneto"), "36": ("Vicenza", "Veneto"), "37": ("Verona", "Veneto"),
        "38": ("Trento", "Trentino-Alto Adige"), "39": ("Bolzano", "Trentino-Alto Adige"),
        "40": ("Bologna", "Emilia-Romagna"), "41": ("Modena", "Emilia-Romagna"),
        "42": ("Reggio Emilia", "Emilia-Romagna"), "43": ("Parma", "Emilia-Romagna"),
        "44": ("Ferrara", "Emilia-Romagna"), "45": ("Rovigo", "Veneto"), "46": ("Mantova", "Lombardia"),
        "47": ("Forli-Cesena", "Emilia-Romagna"), "48": ("Ravenna", "Emilia-Romagna"),
        "50": ("Firenze", "Toscana"), "51": ("Pistoia", "Toscana"), "52": ("Arezzo", "Toscana"),
        "53": ("Siena", "Toscana"), "54": ("Massa-Carrara", "Toscana"), "55": ("Lucca", "Toscana"),
        "56": ("Pisa", "Toscana"), "57": ("Livorno", "Toscana"), "58": ("Grosseto", "Toscana"),
        "59": ("Prato", "Toscana"), "60": ("Ancona", "Marche"), "61": ("Pesaro e Urbino", "Marche"),
        "62": ("Macerata", "Marche"), "63": ("Ascoli Piceno", "Marche"), "64": ("Teramo", "Abruzzo"),
        "65": ("Pescara", "Abruzzo"), "66": ("Chieti", "Abruzzo"), "67": ("L'Aquila", "Abruzzo"),
        "70": ("Bari", "Puglia"), "71": ("Foggia", "Puglia"), "72": ("Brindisi", "Puglia"),
        "73": ("Lecce", "Puglia"), "74": ("Taranto", "Puglia"), "75": ("Matera", "Basilicata"),
        "76": ("BAT", "Puglia"), "80": ("Napoli", "Campania"), "81": ("Caserta", "Campania"),
        "82": ("Benevento", "Campania"), "83": ("Avellino", "Campania"), "84": ("Salerno", "Campania"),
        "85": ("Potenza", "Basilicata"), "86": ("Campobasso", "Molise"), "87": ("Cosenza", "Calabria"),
        "88": ("Catanzaro", "Calabria"), "89": ("Reggio Calabria", "Calabria"), "90": ("Palermo", "Sicilia"),
        "91": ("Trapani", "Sicilia"), "92": ("Agrigento", "Sicilia"), "93": ("Caltanissetta", "Sicilia"),
        "94": ("Enna", "Sicilia"), "95": ("Catania", "Sicilia"), "96": ("Siracusa", "Sicilia"),
        "97": ("Ragusa", "Sicilia"), "98": ("Messina", "Sicilia")
    }

    # --- 2. PULIZIA E DERIVAZIONE GEOGRAFICA ---
    df_clean = df.copy()
    col_cap = 'RNA_CAP_BENEFICIARIO' if 'RNA_CAP_BENEFICIARIO' in df.columns else 'CAP'
    
    # Standardizzazione CAP
    df_clean['CAP_Str'] = df_clean[col_cap].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    df_clean['Prefix'] = df_clean['CAP_Str'].str[:2]
    
    # Derivazione Regione e Provincia
    df_clean['Regione_Pulita'] = df_clean['Prefix'].map(lambda x: geo_db.get(x, (None, "Sconosciuta"))[1])
    df_clean['Provincia_Pulita'] = df_clean['Prefix'].map(lambda x: geo_db.get(x, ("Sconosciuta", None))[0])

    # --- 3. AGGREGAZIONE DATI ---
    df_all = df_clean.groupby('Regione_Pulita')['RNA_ELEMENTO_DI_AIUTO'].agg(['count', 'sum']).reset_index()
    df_all.columns = ['Regione', 'Aiuti_Tot', 'Budget_Tot']

    df_targ_raw = df_clean[df_clean['IS_TARGET'] == 1].copy()
    df_targ_agg = df_targ_raw.groupby('Regione_Pulita')['RNA_ELEMENTO_DI_AIUTO'].agg(['count', 'sum']).reset_index()
    df_targ_agg.columns = ['Regione', 'Aiuti_Targ', 'Budget_Targ']

    # Lista CAP univoci per Regione
    df_caps = df_targ_raw.groupby('Regione_Pulita')['CAP_Str'].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index()
    df_caps.columns = ['Regione', 'Lista_CAP']

    # Unione finale
    df_mappe = pd.merge(df_all, df_targ_agg, on='Regione', how='left')
    df_mappe = pd.merge(df_mappe, df_caps, on='Regione', how='left').fillna(0)

    # Match Key per GeoJSON
    mapping_geo = {
        "Friuli-Venezia Giulia": "friuli venezia giulia",
        "Trentino-Alto Adige": "trentino-alto adige/südtirol",
        "Valle d'Aosta": "valle d'aosta/vallée d'aoste"
    }
    df_mappe['Match_Key'] = df_mappe['Regione'].str.lower()
    for k, v in mapping_geo.items():
        df_mappe.loc[df_mappe['Regione'] == k, 'Match_Key'] = v

    # --- 4. MAPPE E TREEMAP ---
    @st.cache_data
    def get_geojson():
        url = "https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json"
        return requests.get(url).json()
    
    geojson_data = get_geojson()

    def style_map(fig):
        fig.update_geos(visible=True, showland=True, landcolor="#f8f9fa", projection_type='mercator',
                        lataxis_range=[35, 47.5], lonaxis_range=[6, 19])
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450, coloraxis_colorbar_title_text="")
        return fig

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(style_map(px.choropleth(df_mappe, geojson=geojson_data, locations='Match_Key', featureidkey="properties.name",
                                              color='Budget_Tot', color_continuous_scale="Blues", title="💰 Mercato Totale (€)",
                                              labels={'Budget_Tot':'Budget'})), use_container_width=True)
    with c2:
        st.plotly_chart(style_map(px.choropleth(df_mappe, geojson=geojson_data, locations='Match_Key', featureidkey="properties.name",
                                              color='Budget_Targ', color_continuous_scale="Reds", title="🎯 Mercato Target (€)",
                                              labels={'Budget_Targ':'Budget Target'})), use_container_width=True)

    # Treemap
    df_tree = df_targ_raw.groupby(['Regione_Pulita', 'Provincia_Pulita', 'CAP_Str'])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    fig_tree = px.treemap(df_tree, path=[px.Constant("Italia"), 'Regione_Pulita', 'Provincia_Pulita', 'CAP_Str'],
                         values='RNA_ELEMENTO_DI_AIUTO', color='RNA_ELEMENTO_DI_AIUTO', color_continuous_scale='Reds',
                         title="🔍 Drill-down Certificato (Regione > Provincia > CAP)")
    st.plotly_chart(fig_tree, use_container_width=True)

    # --- 5. TABELLA DEFINITIVA ---
    st.write("### 📊 Riepilogo Regionale")
    df_tab = df_mappe[['Regione', 'Match_Key', 'Aiuti_Tot', 'Aiuti_Targ', 'Budget_Tot', 'Budget_Targ', 'Lista_CAP']].sort_values(by='Budget_Targ', ascending=False)
    df_tab.columns = ['Regione', 'Match Key', 'Aiuti Tot', 'Aiuti Target', 'Budget Totale', 'Budget Target', 'Lista CAP Target']

    st.dataframe(
        df_tab.style.background_gradient(cmap='Reds', subset=['Budget Target']),
        use_container_width=True, hide_index=True,
        column_config={
            "Budget Totale": st.column_config.NumberColumn(format="€ %,.0f"),
            "Budget Target": st.column_config.NumberColumn(format="€ %,.0f"),
            "Lista CAP Target": st.column_config.TextColumn(width="large")
        }
    )
