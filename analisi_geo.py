import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    """
    Analisi geografica completa con nomi colonne standardizzati:
    - Mappe con tooltip Nome Regione e Budget Target
    - Tre tabelle: Nazionale, Regionale, Locale con colonne specifiche
    """

    # --- 1. DATABASE DI INTELLIGENCE GEOGRAFICA (CAP -> PROVINCIA, REGIONE) ---
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

    # --- 2. PULIZIA E DERIVAZIONE GEOGRAFICA DA CAP ---
    df_c = df.copy()
    col_cap = 'RNA_CAP_BENEFICIARIO' if 'RNA_CAP_BENEFICIARIO' in df_c.columns else 'CAP'
    col_budget = 'RNA_ELEMENTO_DI_AIUTO' if 'RNA_ELEMENTO_DI_AIUTO' in df_c.columns else 'Budget'
    
    df_c['CAP_Str'] = df_c[col_cap].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    df_c['Prefix'] = df_c['CAP_Str'].str[:2]
    
    df_c['Regione_Auto'] = df_c['Prefix'].map(lambda x: geo_db.get(x, (None, "Sconosciuta"))[1])
    df_c['Provincia_Auto'] = df_c['Prefix'].map(lambda x: geo_db.get(x, ("Sconosciuta", None))[0])
    df_c['Area_CAP'] = "CAP " + df_c['CAP_Str']

    # --- 3. PREPARAZIONE DATI MAPPE ---
    df_naz_agg = df_c.groupby('Regione_Auto')[col_budget].agg(['count', 'sum']).reset_index()
    df_naz_agg.columns = ['Regione', 'Aiuti Totali', 'Budget Totale']

    df_targ_raw = df_c[df_c['IS_TARGET'] == 1].copy()
    df_targ_agg = df_targ_raw.groupby('Regione_Auto')[col_budget].agg(['count', 'sum']).reset_index()
    df_targ_agg.columns = ['Regione', 'Aiuti Target', 'Budget Target']

    df_mappe = pd.merge(df_naz_agg, df_targ_agg, on='Regione', how='left').fillna(0)
    
    df_mappe['Match_Key'] = df_mappe['Regione'].str.lower()
    mapping_geo = {"Friuli-Venezia Giulia": "friuli venezia giulia", "Trentino-Alto Adige": "trentino-alto adige/südtirol", "Valle d'Aosta": "valle d'aosta/vallée d'aoste"}
    for k, v in mapping_geo.items(): df_mappe.loc[df_mappe['Regione'] == k, 'Match_Key'] = v

    @st.cache_data
    def get_geojson(): return requests.get("https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json").json()
    geojson_data = get_geojson()

    def style_map(fig):
        fig.update_geos(visible=True, showland=True, landcolor="#f8f9fa", projection_type='mercator', lataxis_range=[35, 47.5], lonaxis_range=[6, 19])
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450)
        return fig

    # --- 4. MAPPE ---
    c1, c2 = st.columns(2)
    with c1:
        fig_tot = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Match_Key', featureidkey="properties.name",
            color='Budget Totale', color_continuous_scale="Blues", title="💰 Mercato Totale",
            labels={'Regione': 'Nome Regione'},
            hover_name='Regione',
            hover_data={'Match_Key': False, 'Regione': False, 'Budget Totale': ':,.2f €'}
        )
        fig_tot.update_coloraxes(colorbar_title_text="", colorbar_tickformat=".2s")
        st.plotly_chart(style_map(fig_tot), use_container_width=True)

    with c2:
        fig_targ = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Match_Key', featureidkey="properties.name",
            color='Budget Target', color_continuous_scale="Reds", title="🎯 Mercato Target",
            labels={'Regione': 'Nome Regione'},
            hover_name='Regione',
            hover_data={'Match_Key': False, 'Regione': False, 'Budget Target': ':,.2f €'}
        )
        fig_targ.update_coloraxes(colorbar_title_text="", colorbar_tickformat=".2s")
        st.plotly_chart(style_map(fig_targ), use_container_width=True)

    # --- 5. LE TRE TABELLE GERARCHICHE ---
    def get_table_data(groupby_col):
        tot = df_c.groupby(groupby_col)[col_budget].agg(['count', 'sum']).reset_index()
        tot.columns = [groupby_col, 'Aiuti Totali', 'Budget Totale']
        targ = df_c[df_c['IS_TARGET'] == 1].groupby(groupby_col)[col_budget].agg(['count', 'sum']).reset_index()
        targ.columns = [groupby_col, 'Aiuti Target', 'Budget Target']
        final = pd.merge(tot, targ, on=groupby_col, how='left').fillna(0)
        return final.sort_values('Budget Target', ascending=False)

    st.markdown("---")
    
    st.markdown("### 🇮🇹 1. Analisi Nazionale")
    df_naz = get_table_data('Regione_Auto').rename(columns={'Regione_Auto': 'Regione'})
    st.dataframe(df_naz.style.background_gradient(cmap='Reds', subset=['Budget Target']),
                 use_container_width=True, hide_index=True,
                 column_config={"Budget Totale": st.column_config.NumberColumn(format="€ %,.2f"), "Budget Target": st.column_config.NumberColumn(format="€ %,.2f")})

    st.write("")
    st.markdown("### 🏛️ 2. Analisi Regionale")
    df_prov = get_table_data('Provincia_Auto').rename(columns={'Provincia_Auto': 'Provincia'})
    # Inseriamo la Regione per contesto
    reg_map = df_c[['Provincia_Auto', 'Regione_Auto']].drop_duplicates().rename(columns={'Provincia_Auto': 'Provincia', 'Regione_Auto': 'Regione'})
    df_prov = pd.merge(df_prov, reg_map, on='Provincia', how='left')
    df_prov = df_prov[['Regione', 'Provincia', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target']]
    st.dataframe(df_prov.style.background_gradient(cmap='Reds', subset=['Budget Target']),
                 use_container_width=True, hide_index=True,
                 column_config={"Budget Totale": st.column_config.NumberColumn(format="€ %,.2f"), "Budget Target": st.column_config.NumberColumn(format="€ %,.2f")})

    st.write("")
    st.markdown("### 📍 3. Analisi Locale")
    df_loc = get_table_data('Area_CAP').rename(columns={'Area_CAP': 'CAP'})
    loc_map = df_c[['Area_CAP', 'Provincia_Auto', 'Regione_Auto']].drop_duplicates().rename(columns={'Area_CAP': 'CAP', 'Provincia_Auto': 'Provincia', 'Regione_Auto': 'Regione'})
    df_loc = pd.merge(df_loc, loc_map, on='CAP', how='left')
    df_loc = df_loc[['Regione', 'Provincia', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target']]
    st.dataframe(df_loc.style.background_gradient(cmap='Reds', subset=['Budget Target']),
                 use_container_width=True, hide_index=True,
                 column_config={"Budget Totale": st.column_config.NumberColumn(format="€ %,.2f"), "Budget Target": st.column_config.NumberColumn(format="€ %,.2f")})
