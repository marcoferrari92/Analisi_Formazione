import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    """
    Analisi geografica basata su Regione e CAP.
    """
    
    # --- 1. PREPARAZIONE DATI ---
    df_geo_all = df.groupby('RNA_REGIONE_BENEFICIARIO').agg({
        'RNA_TITOLO_MISURA': 'count', 
        'RNA_ELEMENTO_DI_AIUTO': 'sum'
    }).reset_index()
    
    df_geo_target = df[df['IS_TARGET'] == 1].groupby('RNA_REGIONE_BENEFICIARIO').agg({
        'RNA_TITOLO_MISURA': 'count', 
        'RNA_ELEMENTO_DI_AIUTO': 'sum'
    }).reset_index()
    
    df_mappe = pd.merge(
        df_geo_all, df_geo_target, 
        on='RNA_REGIONE_BENEFICIARIO', 
        how='left', 
        suffixes=('_Tot', '_Targ')
    ).fillna(0)
    
    # Mapping GeoJSON (Invariato)
    df_mappe['Regione_Match'] = df_mappe['RNA_REGIONE_BENEFICIARIO'].str.strip().str.lower()
    mapping_geo = {
        "friuli-venezia giulia": "friuli venezia giulia",
        "trentino-alto adige": "trentino-alto adige/südtirol",
        "valle d'aosta": "valle d'aosta/vallée d'aoste"
    }
    df_mappe['Regione_Match'] = df_mappe['Regione_Match'].replace(mapping_geo)

    # --- DATI PER TREEMAP (CAP) ---
    # Usiamo 'RNA_CAP_BENEFICIARIO' (verifica se il nome nel file è esattamente CAP o RNA_CAP_BENEFICIARIO)
    colonna_cap = 'RNA_CAP_BENEFICIARIO' if 'RNA_CAP_BENEFICIARIO' in df.columns else 'CAP'
    
    df_cap = df[df['IS_TARGET'] == 1].groupby(['RNA_REGIONE_BENEFICIARIO', colonna_cap]).agg({
        'RNA_ELEMENTO_DI_AIUTO': 'sum'
    }).reset_index()
    df_cap.columns = ['Regione', 'CAP', 'Budget_Target']
    # Assicuriamoci che il CAP sia trattato come stringa per evitare virgole (es. 20121 invece di 20,121)
    df_cap['CAP'] = df_cap['CAP'].astype(str).str.replace('.0', '', regex=False)

    # --- 2. GEOJSON & STYLE ---
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
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450)
        return fig

    # --- 3. MAPPE ---
    col_map1, col_map2 = st.columns(2)
    with col_map1:
        fig_tot = px.choropleth(df_mappe, geojson=geojson_data, locations='Regione_Match', 
                                featureidkey="properties.name", color='RNA_ELEMENTO_DI_AIUTO_Tot', 
                                color_continuous_scale="Blues", title="💰 Mercato Totale (€)")
        st.plotly_chart(apply_italy_style(fig_tot), use_container_width=True)
    
    with col_map2:
        fig_targ = px.choropleth(df_mappe, geojson=geojson_data, locations='Regione_Match', 
                                 featureidkey="properties.name", color='RNA_ELEMENTO_DI_AIUTO_Targ', 
                                 color_continuous_scale="Reds", title="🎯 Mercato Target (€)")
        st.plotly_chart(apply_italy_style(fig_targ), use_container_width=True)

    # --- 4. TREEMAP (REGIONE -> CAP) ---
    st.write("")
    fig_tree = px.treemap(
        df_cap, 
        path=[px.Constant("Italia"), 'Regione', 'CAP'],
        values='Budget_Target', 
        color='Budget_Target',
        color_continuous_scale='Reds',
        title="Dettaglio per Area (CAP): Clicca su una Regione per i cluster",
        hover_data={'Budget_Target': ':,.0f'}
    )
    fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10), height=500)
    st.plotly_chart(fig_tree, use_container_width=True)

    # --- 5. TABELLA COLORATA ---
    st.write("### 📊 Dettaglio Regionale")
    df_tab = df_mappe[['RNA_REGIONE_BENEFICIARIO', 'RNA_TITOLO_MISURA_Tot', 'RNA_TITOLO_MISURA_Targ', 
                       'RNA_ELEMENTO_DI_AIUTO_Tot', 'RNA_ELEMENTO_DI_AIUTO_Targ']].copy()
    df_tab.columns = ['Regione', 'Aiuti Tot', 'Aiuti Target', 'Budget Totale', 'Budget Target']
    df_tab = df_tab.sort_values(by='Budget Target', ascending=False)
    
    # Formattazione con stile e colori
    st.dataframe(
        df_tab.style.background_gradient(cmap='Reds', subset=['Budget Target']),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget Totale": st.column_config.NumberColumn("Budget Tot (€)", format="€ %,.0f"),
            "Budget Target": st.column_config.NumberColumn("Budget Target (€)", format="€ %,.0f"),
        }
    )
