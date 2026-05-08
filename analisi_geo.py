import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):

    """
    Renderizza l'analisi geografica con mappe, treemap e tabella dati.
    """
    
    # 1. Preparazione Dati
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
    
    df_mappe['Regione_Match'] = df_mappe['RNA_REGIONE_BENEFICIARIO'].str.strip().str.lower()
    
    # Mapping per matchare il GeoJSON
    mapping_geo = {
        "friuli-venezia giulia": "friuli venezia giulia",
        "trentino-alto adige": "trentino-alto adige/südtirol",
        "valle d'aosta": "valle d'aosta/vallée d'aoste"
    }
    df_mappe['Regione_Match'] = df_mappe['Regione_Match'].replace(mapping_geo)
    
    # Scarico GeoJSON (cache inserita per performance)
    @st.cache_data
    def get_geojson():
        url = "https://raw.githubusercontent.com/stefanocudini/leaflet-geojson-selector/master/examples/italy-regions.json"
        return requests.get(url).json()
    
    geojson_data = get_geojson()
    
    # Helper function per lo stile
    def apply_italy_full_style(fig):
        fig.update_geos(
            visible=True,
            showland=True,
            landcolor="#f8f9fa",
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
    
    # --- LAYOUT COLONNE MAPPE ---
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        fig_tot = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Regione_Match', featureidkey="properties.name",
            color='RNA_ELEMENTO_DI_AIUTO_Tot', 
            color_continuous_scale="Blues",
            title="💰 Mercato Totale"
        )
        fig_tot.update_layout(title_x=0.25) 
        st.plotly_chart(apply_italy_full_style(fig_tot), use_container_width=True)
    
    with col_map2:
        fig_targ = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Regione_Match', featureidkey="properties.name",
            color='RNA_ELEMENTO_DI_AIUTO_Targ', 
            color_continuous_scale="Reds",
            title="🎯 Mercato Target"
        )
        fig_targ.update_layout(title_x=0.25)
        st.plotly_chart(apply_italy_full_style(fig_targ), use_container_width=True)
    
    # --- TREEMAP ---
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
    fig_tree.update_layout(
        title_x=0.5, 
        margin=dict(t=50, l=10, r=10, b=10),
        height=400,
        coloraxis_colorbar_title_text=""
    )
    st.plotly_chart(fig_tree, use_container_width=True)
    
    # --- TABELLA ---
    df_reg_tabella = df_mappe.copy()
    df_reg_tabella = df_reg_tabella[[
        'RNA_REGIONE_BENEFICIARIO', 'RNA_TITOLO_MISURA_Tot', 
        'RNA_TITOLO_MISURA_Targ', 'RNA_ELEMENTO_DI_AIUTO_Tot', 'RNA_ELEMENTO_DI_AIUTO_Targ'
    ]]
    df_reg_tabella.columns = ['Regione', 'Aiuti', 'Aiuti Target', 'Budget', 'Budget Target']
    df_reg_tabella = df_reg_tabella.sort_values(by='Budget Target', ascending=False)
    
    st.write("")
    st.dataframe(
        df_reg_tabella,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget": st.column_config.NumberColumn("Budget (€)", format="€ %,.0f"),
            "Budget Target": st.column_config.NumberColumn("Budget Target (€)", format="€ %,.0f"),
        }
    )
