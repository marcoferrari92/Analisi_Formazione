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

    # --- 2. VERIFICA E PULIZIA ---
    df_c = df.copy()
    col_cap = 'CAP' if 'CAP' in df_c.columns else None
    
    if col_cap is None:
        st.warning("⚠️ Colonna CAP non trovata.")
        return df_c

    col_budget = 'RNA_ELEMENTO_DI_AIUTO' if 'RNA_ELEMENTO_DI_AIUTO' in df_c.columns else 'Budget'
    col_piva = 'CF_TROVATO' if 'CF_TROVATO' in df_c.columns else None
    col_rs = 'RAGIONE SOCIALE' if 'RAGIONE SOCIALE' in df_c.columns else None

    # --- 3. CALCOLO LEADERSHIP ---
    
    # Derivazione geo standard
    df_c['CAP_Str'] = df_c[col_cap].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    df_c['Prefix'] = df_c['CAP_Str'].str[:2]
    df_c['Regione'] = df_c['Prefix'].map(lambda x: geo_db.get(x, (None, "Sconosciuta"))[1])
    df_c['Provincia'] = df_c['Prefix'].map(lambda x: geo_db.get(x, ("Sconosciuta", None))[0])
    df_c['CAP'] = df_c['CAP_Str']

    # Solo dati Target per definire la leadership
    df_targ_raw = df_c[df_c['IS_TARGET'] == 1].copy()

    if not df_targ_raw.empty and col_piva:
        
        # A. Leader Nazionale (L'azienda con la somma budget più alta in assoluto)
        naz_totals = df_targ_raw.groupby([col_piva])[col_budget].sum()
        leader_naz_piva = naz_totals.idxmax()

        # B. Leader Regionali
        reg_totals = df_targ_raw.groupby(['Regione', col_piva])[col_budget].sum().reset_index()
        idx_reg = reg_totals.groupby('Regione')[col_budget].idxmax()
        leaders_reg_piva = reg_totals.loc[idx_reg, col_piva].tolist()

        # C. Leader Locali (CAP)
        cap_totals = df_targ_raw.groupby(['CAP', col_piva])[col_budget].sum().reset_index()
        idx_cap = cap_totals.groupby('CAP')[col_budget].idxmax()
        leaders_cap_piva = cap_totals.loc[idx_cap, col_piva].tolist()

        # --- 4. ASSEGNAZIONE ETICHETTE ---
        def check_leadership(row):
            if row[col_piva] == leader_naz_piva:
                return "Leader Nazionale"
            if row[col_piva] in leaders_reg_piva:
                return "Leader Regionale"
            if row[col_piva] in leaders_cap_piva:
                return "Leader Locale"
            return "Competitor"

        df_c['Leadership_Level'] = df_c.apply(check_leadership, axis=1)
    else:
        df_c['Leadership_Level'] = "N/D"

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

    # --- 4. MAPPE A BOLLE (PUNTINI) ---
    st.write("")
    # Creiamo un dataset aggregato per Provincia per avere più "puntini" sparsi
    df_bubbles = df_c.groupby(['Regione', 'Provincia'])[col_budget].agg(['count', 'sum']).reset_index()
    df_bubbles.columns = ['Regione', 'Provincia', 'Aiuti', 'Budget']
    
    # Dati Target per i puntini rossi
    df_bubbles_t = df_targ_raw.groupby(['Regione', 'Provincia'])[col_budget].agg(['count', 'sum']).reset_index()
    df_bubbles_t.columns = ['Regione', 'Provincia', 'Aiuti Target', 'Budget Target']

    c1, c2 = st.columns(2)
    
    with c1:
        # Nota: scatter_geo senza lat/lon usa i nomi delle regioni/stati. 
        # Per i puntini precisi servirebbe un file di coordinate.
        fig_tot = px.scatter_geo(df_bubbles, 
                                locations='Regione', # Plotly centrerà la bolla sulla regione
                                locationmode='country names', # o usare lat/lon se le avessi
                                size='Budget', 
                                hover_name='Provincia',
                                title="💰 Mercato Totale",
                                template='plotly_white')
        
        # Se non hai lat/lon, scatter_geo su mappa Italia è limitato. 
        # Di solito si preferisce mantenere il Choropleth (quello di prima) e 
        # AGGIUNGERE i punti sopra. Ma Plotly Express non lo permette facilmente in un colpo solo.
        
        st.plotly_chart(style_map(fig_tot), use_container_width=True)

    with c2:
        fig_targ = px.scatter_geo(df_bubbles_t, 
                                 locations='Regione',
                                 size='Budget Target', 
                                 color_discrete_sequence=['red'],
                                 hover_name='Provincia',
                                 title="🎯 Mercato Target")
        
        st.plotly_chart(style_map(fig_targ), use_container_width=True)

    

    # --- 5. TREEMAP CON LEADER (Senza Quota) ---
    st.write("")
    if not df_targ_raw.empty:
        st.write("")
        st.markdown("### 🔍 Drill-down Geografico")

        # 1. Identificazione Leader per CAP
        cap_leader_data = df_targ_raw.groupby(['Regione', 'Provincia', 'CAP', col_piva, col_rs])[col_budget].sum().reset_index()
        idx_max = cap_leader_data.groupby(['Regione', 'Provincia', 'CAP'])[col_budget].idxmax()
        cap_leaders = cap_leader_data.loc[idx_max].rename(columns={col_rs: 'Leader_Nome', col_budget: 'Leader_Budget'})

        # 2. Dataset per Treemap
        df_tree_agg = df_targ_raw.groupby(['Regione', 'Provincia', 'CAP'])[col_budget].sum().reset_index()
        df_tree_agg.columns = ['Regione', 'Provincia', 'CAP', 'Budget_Target']
        df_tree_final = pd.merge(df_tree_agg, cap_leaders[['CAP', 'Leader_Nome', 'Leader_Budget']], on='CAP', how='left')
        
        # 3. Creazione Grafico
        fig_tree = px.treemap(
            df_tree_final, 
            path=[px.Constant("Italia"), 'Regione', 'Provincia', 'CAP'],
            values='Budget_Target', 
            color='Budget_Target', 
            color_continuous_scale='Reds',
            custom_data=['Leader_Nome', 'Leader_Budget']
        )

        # 4. Hovertemplate semplificato
        h_text = "<b>%{label}</b><br>Budget Target Nodo: € %{value:,.2f}<br>🏆 Leader CAP: %{customdata[0]}<br>Budget Leader: € %{customdata[1]:,.2f}<extra></extra>"
        
        fig_tree.update_traces(hovertemplate=h_text)
        fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=600)
        st.plotly_chart(fig_tree, use_container_width=True)

    # --- 6. FUNZIONE AGGREGAZIONE TABELLE ---
    def get_table_data(groupby_col):
        tot = df_c.groupby(groupby_col)[col_budget].agg(['count', 'sum']).reset_index().rename(columns={'count':'Aiuti Totali', 'sum':'Budget Totale'})
        targ = df_targ_raw.groupby(groupby_col)[col_budget].agg(['count', 'sum']).reset_index().rename(columns={'count':'Aiuti Target', 'sum':'Budget Target'})
        final = pd.merge(tot, targ, on=groupby_col, how='left').fillna(0)
        
        if col_piva and col_rs:
            company_totals = df_targ_raw.groupby([groupby_col, col_piva, col_rs])[col_budget].sum().reset_index()
            idx_max_t = company_totals.groupby(groupby_col)[col_budget].idxmax()
            leaders = company_totals.loc[idx_max_t].rename(columns={col_rs: 'Azienda Leader', col_budget: 'Budget Leader'})
            final = pd.merge(final, leaders[[groupby_col, 'Azienda Leader', 'Budget Leader']], on=groupby_col, how='left')
            final['Budget (%)'] = (final['Budget Leader'] / final['Budget Target']).fillna(0)
        return final.sort_values('Budget Target', ascending=False)

    common_config = {
        "Aiuti Totali": st.column_config.NumberColumn(format="%d"),
        "Aiuti Target": st.column_config.NumberColumn(format="%d"),
        "Budget Totale": st.column_config.NumberColumn(format="€ %,.2f"),
        "Budget Target": st.column_config.NumberColumn(format="€ %,.2f"),
        "Budget Leader": st.column_config.NumberColumn("Budget Leader", format="€ %,.2f"),
        "Budget (%)": st.column_config.ProgressColumn("Budget (%)", format="%.1f%%", min_value=0, max_value=1)
    }

    # --- 7. VISUALIZZAZIONE TABELLE ---
    st.write("")
    st.write("")
    st.write("### 🇮🇹 Analisi Nazionale")
    df_naz = get_table_data('Regione')[['Regione', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target', 'Azienda Leader', 'Budget Leader', 'Budget (%)']]
    st.dataframe(df_naz.style.background_gradient(cmap='Reds', subset=['Budget Target']), use_container_width=True, hide_index=True, column_config=common_config)

    st.write("")
    st.write("")
    st.write("### 🏛️ Analisi Regionale")
    df_prov = get_table_data('Provincia')
    df_prov = pd.merge(df_prov, df_c[['Provincia', 'Regione']].drop_duplicates(), on='Provincia', how='left')
    df_prov = df_prov[['Regione', 'Provincia', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target', 'Azienda Leader', 'Budget Leader', 'Budget (%)']]
    st.dataframe(df_prov.style.background_gradient(cmap='Reds', subset=['Budget Target']), use_container_width=True, hide_index=True, column_config=common_config)

    st.write("")
    st.write("")
    st.write("### 📍 Analisi Locale")
    df_loc = get_table_data('CAP')
    df_loc = pd.merge(df_loc, df_c[['CAP', 'Provincia', 'Regione']].drop_duplicates(), on='CAP', how='left')
    df_loc = df_loc[['Regione', 'Provincia', 'CAP', 'Aiuti Totali', 'Budget Totale', 'Aiuti Target', 'Budget Target', 'Azienda Leader', 'Budget Leader', 'Budget (%)']]
    st.dataframe(df_loc.style.background_gradient(cmap='Reds', subset=['Budget Target']), use_container_width=True, hide_index=True, column_config=common_config)


    # --- NUOVA SEZIONE: ANALISI SATURAZIONE E POTENZIALE ---
    st.markdown("---")
    st.markdown("### 🌡️ Analisi Saturazione e Aree Fredde")

    # 1. Calcolo Saturazione per Provincia
    # (Riusiamo df_bubbles e df_bubbles_t calcolati per le mappe)
    df_sat = pd.merge(df_bubbles, df_bubbles_t, on=['Regione', 'Provincia'], how='left').fillna(0)
    
    # Calcolo % Saturazione (Target su Totale)
    df_sat['Saturazione (%)'] = (df_sat['Budget Target'] / df_sat['Budget']) * 100
    
    # Media Nazionale per confronto
    media_naz_sat = df_sat['Saturazione (%)'].mean()

    # 2. Introduzione Variabile "Dimensione Mercato" (Proxy Popolazione/Volume)
    # Usiamo la mediana del Budget Totale come soglia per definire aree "Grandi" o "Piccole"
    soglia_mediana = df_sat['Budget'].median()

    def classify_area(row):
        if row['Budget'] >= soglia_mediana:
            return "Mercato Grande" if row['Saturazione (%)'] >= media_naz_sat else "POTENZIALE ALTO (Area Fredda)"
        else:
            return "Mercato Nicchia" if row['Saturazione (%)'] >= media_naz_sat else "Area Marginale"

    df_sat['Classificazione'] = df_sat.apply(classify_area, axis=1)

    # 3. Visualizzazione: Mappa della Saturazione
    fig_sat = px.choropleth(
        df_sat, geojson=geojson_data, locations='Regione', 
        locationmode='country names', # Nota: qui andrebbe Match_Key se usi il geojson precedente
        color='Saturazione (%)',
        color_continuous_scale='RdYlGn',
        title="Mappa della Saturazione (Verde = Alta Quota Target, Rosso = Bassa)",
        hover_name='Provincia',
        hover_data=['Budget', 'Budget Target', 'Classificazione']
    )
    st.plotly_chart(fig_sat, use_container_width=True)

    # 4. Tabella Opportunità (Le vere "Aree Fredde" ad alto budget)
    st.markdown("#### 🎯 Focus: Aree con Alto Budget Totale ma Bassa Saturazione Target")
    
    # Filtriamo le aree dove il budget totale è sopra la mediana (mercato ricco) 
    # ma la saturazione è sotto la media nazionale (poco target)
    df_opportunita = df_sat[
        (df_sat['Budget'] > soglia_mediana) & 
        (df_sat['Saturazione (%)'] < media_naz_sat)
    ].sort_values('Budget', ascending=False)

    col_sat_config = {
        "Budget": st.column_config.NumberColumn("Mercato Totale", format="€ %,.2f"),
        "Budget Target": st.column_config.NumberColumn("Mercato Target", format="€ %,.2f"),
        "Saturazione (%)": st.column_config.NumberColumn("Quota Target", format="%.1f%%"),
        "Classificazione": st.column_config.TextColumn("Status")
    }

    st.dataframe(
        df_opportunita[['Regione', 'Provincia', 'Budget', 'Budget Target', 'Saturazione (%)', 'Classificazione']],
        use_container_width=True,
        hide_index=True,
        column_config=col_sat_config
    )

    
    st.success("Analisi completata con Leadership Level")
    
    # Restituiamo il dataframe arricchito
    return df_c
