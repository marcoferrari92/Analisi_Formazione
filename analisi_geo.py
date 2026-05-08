import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    # --- 1. DIZIONARIO DI DECODIFICA CAP -> PROVINCIA (Sintetico) ---
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
    
    df_tree_raw = df[df['IS_TARGET'] == 1].groupby(['RNA_REGIONE_BENEFICIARIO', colonna_cap]).agg({
        'RNA_ELEMENTO_DI_AIUTO': 'sum'
    }).reset_index()
    df_tree_raw.columns = ['Regione', 'CAP_Raw', 'Budget_Target']
    
    # Pulizia CAP e creazione Provincia
    df_tree_raw['CAP_Str'] = df_tree_raw['CAP_Raw'].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    df_tree_raw['Prefix'] = df_tree_raw['CAP_Str'].str[:2]
    
    # Assegnazione Nome Provincia: se non trova il prefisso nel dizionario, mette "Area " + prefisso
    df_tree_raw['Provincia'] = df_tree_raw['Prefix'].map(cap_to_prov).fillna("Area " + df_tree_raw['Prefix'])
    
    # Creiamo l'etichetta finale del CAP per la treemap
    df_tree_raw['CAP_Label'] = "CAP " + df_tree_raw['CAP_Str']

    # --- 3. MAPPE AFFIANCATE ---
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        fig_tot = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Regione_Match', 
            featureidkey="properties.name", 
            color='RNA_ELEMENTO_DI_AIUTO_Tot', 
            color_continuous_scale="Blues", 
            title="💰 Mercato Totale (€)",
            labels={'RNA_ELEMENTO_DI_AIUTO_Tot': 'Budget'} # Label richiesta
        )
        st.plotly_chart(apply_italy_style(fig_tot), use_container_width=True)
    
    with col_map2:
        fig_targ = px.choropleth(
            df_mappe, geojson=geojson_data, locations='Regione_Match', 
            featureidkey="properties.name", 
            color='RNA_ELEMENTO_DI_AIUTO_Targ', 
            color_continuous_scale="Reds", 
            title="🎯 Mercato Target (€)",
            labels={'RNA_ELEMENTO_DI_AIUTO_Targ': 'Budget Target'} # Label richiesta
        )
        st.plotly_chart(apply_italy_style(fig_targ), use_container_width=True)

    # --- 4. TREEMAP CON DOPPIA ESPLOSIONE AUTOMATICA ---
    st.write("### 🔍 Esplosione Geografica (Regione > Provincia > CAP)")
    fig_tree = px.treemap(
        df_tree_raw, 
        path=[px.Constant("Italia"), 'Regione', 'Provincia', 'CAP_Label'],
        values='Budget_Target', 
        color='Budget_Target',
        color_continuous_scale='Reds',
        title="Dettaglio Gerarchico: Clicca per esplorare",
        labels={'Budget_Target': 'Budget', 'CAP_Label': 'CAP'},
        hover_data={'Budget_Target': ':,.0f'}
    )
    fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10), height=600)
    st.plotly_chart(fig_tree, use_container_width=True, key="tree_drilldown")

    # --- 5. TABELLA ANALITICA CON GRADIENTE ---
    st.write("### 📊 Dettaglio Regionale (Ordinato per Budget Target)")
    
    df_tab = df_mappe[[
        'RNA_REGIONE_BENEFICIARIO', 'RNA_TITOLO_MISURA_Tot', 'RNA_TITOLO_MISURA_Targ', 
        'RNA_ELEMENTO_DI_AIUTO_Tot', 'RNA_ELEMENTO_DI_AIUTO_Targ'
    ]].copy()
    
    df_tab.columns = ['Regione', 'Aiuti Tot', 'Aiuti Target', 'Budget Totale', 'Budget Target']
    
    # Ordinamento primario richiesto
    df_tab = df_tab.sort_values(by='Budget Target', ascending=False)
    
    # Applicazione stile con gradiente Rosso coerente con le mappe
    st.dataframe(
        df_tab.style.background_gradient(cmap='Reds', subset=['Budget Target']),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget Totale": st.column_config.NumberColumn("Budget Tot (€)", format="€ %,.0f"),
            "Budget Target": st.column_config.NumberColumn("Budget Target (€)", format="€ %,.0f"),
            "Aiuti Tot": st.column_config.NumberColumn("Aiuti Tot", format="%d"),
            "Aiuti Target": st.column_config.NumberColumn("Aiuti Target", format="%d")
        }
    )
