import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def geo_analysis(df):
    """
    Analisi geografica definitiva con:
    - Leader identificato tramite P.IVA (CF_TROVATO)
    - Visualizzazione Ragione Sociale nelle tabelle
    - Tre livelli: Nazionale, Regionale, Locale (CAP)
    """

    # --- 1. DATABASE DI INTELLIGENCE GEOGRAFICA ---
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
    df_c = df.copy()
    col_cap = 'RNA_CAP_BENEFICIARIO' if 'RNA_CAP_BENEFICIARIO' in df_c.columns else 'CAP'
    col_budget = 'RNA_ELEMENTO_DI_AIUTO' if 'RNA_ELEMENTO_DI_AIUTO' in df_c.columns else 'Budget'
    
    # Identificazione colonne azienda
    col_piva = 'CF_TROVATO' if 'CF_TROVATO' in df_c.columns else None
    col_rs = 'RAGIONE SOCIALE' if 'RAGIONE SOCIALE' in df_c.columns else None
    
    df_c['CAP_Str'] = df_c[col_cap].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    df_c['Prefix'] = df_c['CAP_Str'].str[:2]
    
    df_c['Regione'] = df_c['Prefix'].map(lambda x: geo_db.get(x, (None, "Sconosciuta"))[1])
    df_c['Provincia'] = df_c['Prefix'].map(lambda x: geo_db.get(x, ("Sconosciuta", None))[0])
    df_c['CAP'] = df_c['CAP_Str']

    # --- 3. PREPARAZIONE DATI MAPPE ---
    df_naz_agg = df_c.groupby('Regione')[col_budget].agg(['count', 'sum']).reset_index()
    df_naz_agg.columns = ['Regione', 'Aiuti Totali', 'Budget Totale']

    df_targ_raw = df_c[df_c['IS_TARGET'] == 1].copy()
    df_targ_agg = df_targ_raw.groupby('Regione')[col_budget].agg(['count', 'sum']).reset_index()
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
        fig_tot = px.choropleth(df_mappe, geojson=geojson_data, locations='Match_Key', featureidkey="properties.name",
                                color='Budget Totale', color_continuous_scale="Blues", title="💰 Mercato Totale",
                                hover_name='Regione', hover_data={'Match_Key': False, 'Budget Totale': False})
        fig_tot.update_traces(hovertemplate="<b>%{hovertext}</b><br>Budget Totale: € %{z:,.2f}<extra></extra>")
        fig_tot.update_coloraxes(colorbar_title_text="", colorbar_tickformat=".2s")
        st.plotly_chart(style_map(fig_tot), use_container_width=True)

    with c2:
        fig_targ = px.choropleth(df_mappe, geojson=geojson_data, locations='Match_Key', featureidkey="properties.name",
                                 color='Budget Target', color_continuous_scale="Reds", title="🎯 Mercato Target",
                                 hover_name='Regione', hover_data={'Match_Key': False, 'Budget Target': False})
        fig_targ.update_traces(hovertemplate="<b>%{hovertext}</b><br>Budget Target: € %{z:,.2f}<extra></extra>")
        fig_targ.update_coloraxes(colorbar_title_text="", colorbar_tickformat=".2s")
        st.plotly_chart(style_map(fig_targ), use_container_width=True)

    
    # --- 5. TREEMAP CON LEADER E QUOTE ---
    st.write("")
    st.markdown("### 🔍 Drill-down Geografico")

    # 1. Prepariamo i dati a livello CAP includendo il Leader per quel CAP
    # Sommiamo il budget target per azienda dentro ogni CAP
    cap_leader_data = df_targ_raw.groupby(['Regione', 'Provincia', 'CAP', col_piva, col_rs])[col_budget].sum().reset_index()
    
    # Identifichiamo il leader per ogni CAP
    idx_max = cap_leader_data.groupby(['Regione', 'Provincia', 'CAP'])[col_budget].idxmax()
    cap_leaders = cap_leader_data.loc[idx_max].rename(columns={
        col_rs: 'Leader_Nome', 
        col_budget: 'Leader_Budget'})

    # 2. Prepariamo il dataframe per la treemap (totale budget target per CAP)
    df_tree_agg = df_targ_raw.groupby(['Regione', 'Provincia', 'CAP'])[col_budget].sum().reset_index()
    df_tree_agg.columns = ['Regione', 'Provincia', 'CAP', 'Budget_Target']

    # Uniamo le info del leader
    df_tree_final = pd.merge(df_tree_agg, cap_leaders[['CAP', 'Leader_Nome', 'Leader_Budget']], on='CAP', how='left')
    
    # 3. Calcoliamo i totali regionali per le quote (opzionale, ma utile per il calcolo dinamico)
    # Nota: Plotly calcola le somme dei rami automaticamente, quindi usiamo custom_data per passare i valori fissi del leader
    
    fig_tree = px.treemap(
        df_tree_final, 
        path=[px.Constant("Italia"), 'Regione', 'Provincia', 'CAP'],
        values='Budget_Target', 
        color='Budget_Target', 
        color_continuous_scale='Reds',
        custom_data=['Leader_Nome', 'Leader_Budget', 'Budget_Target']
    )

    # 4. Hovertemplate personalizzato
    # %{value} è il budget del nodo corrente
    # %{parent} o calcoli manuali per le quote
    fig_tree.update_traces(
        hovertemplate="""
        <b>%{label}</b><br>
        Budget Target Nodo: € %{value:,.2f}<br>
        -------------------------<br>
        🏆 Leader Area (CAP): %{customdata[0]}<br>
        Budget Leader: € %{customdata[1]:,.2f}<br>
        Quota Leader su CAP: %{customdata[1]/customdata[2]:.1%}<br>
        <extra></extra>
        """
    )

    fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=600, coloraxis_colorbar_title_text="")
    st.plotly_chart(fig_tree, use_container_width=True)


    # --- 4. FUNZIONE AGGREGAZIONE TABELLE ---
    def get_table_data(groupby_col):
        # Base
        tot = df_c.groupby(groupby_col)[col_budget].agg(['count', 'sum']).reset_index().rename(columns={'count':'Aiuti Totali', 'sum':'Budget Totale'})
        targ = df_targ_raw.groupby(groupby_col)[col_budget].agg(['count', 'sum']).reset_index().rename(columns={'count':'Aiuti Target', 'sum':'Budget Target'})
        final = pd.merge(tot, targ, on=groupby_col, how='left').fillna(0)
        
        # Leader Logic
        if col_piva and col_rs:
            company_totals = df_targ_raw.groupby([groupby_col, col_piva, col_rs])[col_budget].sum().reset_index()
            idx_max = company_totals.groupby(groupby_col)[col_budget].idxmax()
            leaders = company_totals.loc[idx_max].rename(columns={col_rs: 'Azienda Leader', col_budget: 'Budget Leader'})
            final = pd.merge(final, leaders[[groupby_col, 'Azienda Leader', 'Budget Leader']], on=groupby_col, how='left')
            final['Budget (%)'] = (final['Budget Leader'] / final['Budget Target']).fillna(0)
        return final.sort_values('Budget Target', ascending=False)

    # Configurazione Colonne
    common_config = {
        "Aiuti Totali": st.column_config.NumberColumn(format="%d"),
        "Aiuti Target": st.column_config.NumberColumn(format="%d"),
        "Budget Totale": st.column_config.NumberColumn(format="€ %,.2f"),
        "Budget Target": st.column_config.NumberColumn(format="€ %,.2f"),
        "Budget Leader": st.column_config.NumberColumn("Budget Leader", format="€ %,.2f"),
        "Budget (%)": st.column_config.ProgressColumn("Budget (%)", format="%.1f%%", min_value=0, max_value=1)
    }

    # --- 5. VISUALIZZAZIONE TABELLE ---
    st.write("")
    st.write("")
    st.markdown("### 🇮🇹 Analisi Nazionale")
    df_naz = get_table_data('Regione')[['Regione', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target', 'Azienda Leader', 'Budget Leader', 'Budget (%)']]
    st.dataframe(df_naz.style.background_gradient(cmap='Reds', subset=['Budget Target']), use_container_width=True, hide_index=True, column_config=common_config)

    st.write("")
    st.markdown("### 🏛️ Analisi Regionale")
    df_prov = get_table_data('Provincia')
    df_prov = pd.merge(df_prov, df_c[['Provincia', 'Regione']].drop_duplicates(), on='Provincia', how='left')
    df_prov = df_prov[['Regione', 'Provincia', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target', 'Azienda Leader', 'Budget Leader', 'Budget (%)']]
    st.dataframe(df_prov.style.background_gradient(cmap='Reds', subset=['Budget Target']), use_container_width=True, hide_index=True, column_config=common_config)

    st.write("")
    st.markdown("### 📍 Analisi Locale")
    df_loc = get_table_data('CAP')
    df_loc = pd.merge(df_loc, df_c[['CAP', 'Provincia', 'Regione']].drop_duplicates(), on='CAP', how='left')
    df_loc = df_loc[['Regione', 'Provincia', 'CAP', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target', 'Azienda Leader', 'Budget Leader', 'Budget (%)']]
    st.dataframe(df_loc.style.background_gradient(cmap='Reds', subset=['Budget Target']), use_container_width=True, hide_index=True, column_config=common_config) 
