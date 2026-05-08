import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    """
    Renderizza l'analisi geografica con mappe sincronizzate, 
    treemap esplorabile (Regione -> Comune) e tabella formattata.
    """
    
    # --- 1. PREPARAZIONE DATI ---
    # Dati aggregati per Regione (Generale e Target)
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
    
    # Preparazione per il mapping GeoJSON
    df_mappe['Regione_Match'] = df_mappe['RNA_REGIONE_BENEFICIARIO'].str.strip().str.lower()
    mapping_geo = {
        "friuli-venezia giulia": "friuli venezia giulia",
        "trentino-alto adige": "trentino-alto adige/südtirol",
        "valle d'aosta": "valle d'aosta/vallée d'aoste"
    }
    df_mappe['Regione_Match'] = df_mappe['Regione_Match'].replace(mapping_geo)

    # Dati per Treemap (Dettaglio Comune)
    df_citta = df[df['IS_TARGET'] == 1].groupby(['RNA_REGIONE_BENEFICIARIO', 'RNA_COMUNE_BENEFICIARIO']).agg({
        'RNA_ELEMENTO_DI_AIUTO': 'sum'
    }).reset_index()
    df_citta.columns = ['Regione', 'Comune', 'Budget_Target']

    # --- 2. CARICAMENTO GEOJSON ---
    @st.cache_data
    def get_geojson():
        url = "https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json"
        return requests.get(url).json()
    
    geojson_data = get_geojson()

    # Helper per lo stile mappe
    def apply_italy_style(fig):
        fig.update_geos(
            visible=True, showland=True, landcolor="#f8f9fa",
            showcoastlines=True, projection_type='mercator',
            lataxis_range=[35, 47.5], lonaxis_range=[6, 19]
        )
        fig.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0}, height=450,
            coloraxis_showscale=True, coloraxis_colorbar_title_text=""
        )
        return fig

    # --- 3. LAYOUT: MAPPE AFFIANCATE ---
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        fig_tot = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Regione_Match', featureidkey="properties.name",
            color='RNA_ELEMENTO_DI_AIUTO_Tot', color_continuous_scale="Blues",
            title="💰 Mercato Totale (€)"
        )
        st.plotly_chart(apply_italy_style(fig_tot), use_container_width=True)
    
    with col_map2:
        fig_targ = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Regione_Match', featureidkey="properties.name",
            color='RNA_ELEMENTO_DI_AIUTO_Targ', color_continuous_scale="Reds",
            title="🎯 Mercato Target (€)"
        )
        st.plotly_chart(apply_italy_style(fig_targ), use_container_width=True)

    # --- 4. TREEMAP ESPLORABILE (REGIONE -> COMUNE) ---
    st.write("")
    fig_tree = px.treemap(
        df_citta, 
        path=[px.Constant("Italia"), 'Regione', 'Comune'],
        values='Budget_Target', 
        color='Budget_Target',
        color_continuous_scale='Reds',
        title="Distribuzione Budget: Clicca su una Regione per esplorare le Città",
        hover_data={'Budget_Target': ':,.0f'}
    )
    fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10), height=500)
    st.plotly_chart(fig_tree, use_container_width=True)

    # --- 5. TABELLA ANALITICA CON COLORAZIONE ---
    st.write("### 📊 Dettaglio Regionale (Ordinato per Budget Target)")
    
    # Pulizia e ordinamento tabella
    df_tab = df_mappe[[
        'RNA_REGIONE_BENEFICIARIO', 'RNA_TITOLO_MISURA_Tot', 
        'RNA_TITOLO_MISURA_Targ', 'RNA_ELEMENTO_DI_AIUTO_Tot', 'RNA_ELEMENTO_DI_AIUTO_Targ'
    ]].copy()
    df_tab.columns = ['Regione', 'Aiuti Tot', 'Aiuti Target', 'Budget Totale', 'Budget Target']
    
    # Ordinamento per Budget Target decrescente
    df_tab = df_tab.sort_values(by='Budget Target', ascending=False)
    
    # Visualizzazione con Background Gradient (Scala Reds per il Budget Target)
    st.dataframe(
        df_tab.style.background_gradient(cmap='Reds', subset=['Budget Target']),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget Totale": st.column_config.NumberColumn("Budget Totale (€)", format="€ %,.0f"),
            "Budget Target": st.column_config.NumberColumn("Budget Target (€)", format="€ %,.0f"),
            "Aiuti Tot": st.column_config.NumberColumn("Aiuti Tot", format="%d"),
            "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d")
        }
    )
