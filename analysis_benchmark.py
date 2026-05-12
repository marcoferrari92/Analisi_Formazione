import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def grafici_posizionamento(df_plot, med_Fo, med_Fe, custom_data, custom_template):
    
    from plots import plot_scatter_median
    from settings import STRATEGIA_BENCHMARK
    
    if df_plot.empty:
        st.warning("Nessun dato disponibile per l'analisi degli outlier.")
        return

    st.write("")

    with st.expander("📊 Grafici specializzazione"):

        with st.popover("💡 Strategia"):
            st.info(STRATEGIA_BENCHMARK)
    
        # --- 1. RIGA DEI GRAFICI 2D (OPERATIVO E ECONOMICO) ---
        col_graf_1, col_graf_2 = st.columns(2)
        
        with col_graf_1:
            fig_op = plot_scatter_median(
                df=df_plot, 
                x_col="Aiuti", 
                y_col="Aiuti Target", 
                color_col="Fo", 
                title="Specializzazione Operativa (N. Aiuti)", 
                med_val=med_Fo, 
                custom_data=custom_data, 
                hover_template=custom_template,
                size_col="Budget Target",
                line_color="Red",   
                x_log = False,  
                y_log = False
            )
            st.plotly_chart(fig_op, use_container_width=True)
            if med_Fo > 0:
                st.caption(f"La linea rossa rappresenta la Mediana Fo ({med_Fo:.1f}%)")
                st.caption(f"Dimensione pallini: Budget Target")
            
        with col_graf_2:
            fig_ec = plot_scatter_median(
                df=df_plot, 
                x_col="Budget", 
                y_col="Budget Target", 
                color_col="Fe",
                title="Specializzazione Economica (Budget)", 
                med_val=med_Fe, 
                custom_data=custom_data, 
                size_col="Aiuti Target",
                hover_template=custom_template, 
                line_color="Blue", 
                x_log=True,
                y_log=True 
            )
            st.plotly_chart(fig_ec, use_container_width=True)
            if med_Fe > 0:
                st.caption(f"La linea blu rappresenta la Mediana Fe ({med_Fe:.1f}%)")
                st.caption(f"Dimensione pallini: Num. Aiuti Target")
    
        
        # --- 2. GRAFICO CONFRONTO TARGET ---
        df_plot['Sqrt_Budget'] = np.sqrt(df_plot['Budget'])
        st.write("")
        fig_vs = plot_scatter_median(
                df=df_plot, 
                x_col="Budget Target", 
                y_col="Aiuti Target", 
                color_col="Aiuti",
                title="Confronto Specializzazioni: Num. Aiuti Target vs Budget Target", 
                med_val=0, 
                custom_data=custom_data, 
                size_col="Sqrt_Budget",
                hover_template=custom_template, 
                line_color="Blue", 
                x_log = True,
                y_log = False
        )
    
        # Iniezione dei quadranti basati sulle mediane assolute
        
        med_abs_budget_target = df_plot['Budget Target'].median()
        med_abs_aiuti_target = df_plot['Aiuti Target'].median()
        
        fig_vs.add_hline(y=med_abs_aiuti_target, line_dash="dot", line_color="red", 
                         annotation_text=f"Mediana Aiuti ({med_abs_aiuti_target:.0f})", 
                         annotation_position="bottom right")
        
        fig_vs.add_vline(x=med_abs_budget_target, line_dash="dot", line_color="blue", 
                         annotation_text=f"Mediana Budget (€ {med_abs_budget_target:,.0f})", 
                         annotation_position="top left")
    
        # Assicuriamoci che l'asse X parta da un valore positivo (>0), 
        # altrimenti il logaritmo fallisce e le annotazioni spariscono.
        x_min = df_plot['Budget Target'][df_plot['Budget Target'] > 0].min() * 0.5
        x_max = df_plot['Budget Target'].max() * 1.5
        
        st.plotly_chart(fig_vs, use_container_width=True)
        st.caption("Colore del pallino: Num. Aiuti Totale")
        st.caption("Dimensione del pallino: radice quadrata del Budget Totale")
    
    
        # --- NUOVA SEZIONE: QUADRANTE DI EFFICIENZA (INTEGRATA) ---
        st.write("")
            
        # Usiamo df_plot che ha già i dati filtrati necessari
        fig_quad = plot_scatter_median(
            df=df_plot,
            x_col='Fo',
            y_col='Fe',
            color_col='Aiuti Target',
            size_col='Budget Target',
            title="Confronto specializzazioni: Fo vs Fe",
            med_val=0, 
            custom_data=custom_data,
            hover_template=custom_template
        )
    
        # Iniezione delle linee dei quadranti
        fig_quad.add_hline(y=med_Fe, line_dash="dot", line_color="blue", 
                           annotation_text=f"Mediana Fe ({med_Fe:.1f}%)", annotation_position="bottom right")
        fig_quad.add_vline(x=med_Fo, line_dash="dot", line_color="red", 
                           annotation_text=f"Mediana Fo ({med_Fo:.1f}%)", annotation_position="top left")
    
        fig_quad.update_layout(
            xaxis=dict(range=[-5, 105], ticksuffix="%"),
            yaxis=dict(range=[-5, 105], ticksuffix="%"),
            height=600
        )
    
        st.plotly_chart(fig_quad, use_container_width=True, key="quadrante_efficienza_internal")
        st.caption(f"La linea rossa rappresenta la Mediana Fo ({med_Fo:.1f}%)")
        st.caption(f"La linea blu rappresenta la Mediana Fe ({med_Fe:.1f}%)")
        st.caption(f"Dimensione pallini: Budget Target")

        
st.write("")





# ***********************
    # FREQUENZE AIUTI TARGET 
    # ***********************
    
    st.divider()
    st.subheader("🏢 Analisi Frequenze e Vivacità Target")
    
    # 1. Filtro e Metriche TOTALI
    df_temp_filtrato = df_temp[df_temp['RNA_ELEMENTO_DI_AIUTO'] > 0].copy()
    analisi_tot = df_temp_filtrato.groupby('CF_TROVATO').agg({
        'CF_TROVATO': 'count',
        'RNA_DATA_CONCESSIONE': ['min', 'max']
    })
    analisi_tot.columns = ['N° Aiuti Tot', 'Primo Aiuto', 'Ultimo Aiuto']
    analisi_tot = analisi_tot.reset_index()
    
    # Calcolo Freq. Totale
    diff_date_tot = (analisi_tot['Ultimo Aiuto'] - analisi_tot['Primo Aiuto']).dt.days
    analisi_tot['Freq. Aiuti (gg)'] = diff_date_tot / (analisi_tot['N° Aiuti Tot'] - 1)
    analisi_tot['Freq. Aiuti (gg)'] = analisi_tot['Freq. Aiuti (gg)'].replace([float('inf'), -float('inf')], pd.NA)

    # 2. Metriche settore TARGET
    df_target = df_temp_filtrato[df_temp_filtrato['IS_TARGET'] == 1].copy()
    
    if not df_target.empty:
        analisi_target = df_target.groupby('CF_TROVATO').agg({
            'RAGIONE SOCIALE': 'first',
            'RNA_ELEMENTO_DI_AIUTO': 'sum',
            'CF_TROVATO': 'count',
            'RNA_DATA_CONCESSIONE': ['min', 'max']
        })
        analisi_target.columns = ['Ragione Sociale', 'Budget Target (€)', 'N° Aiuti Target', 'Primo Target', 'Ultimo Target']
        analisi_target = analisi_target.reset_index()
        
        oggi_dt = dt.datetime.now()
        analisi_target['Ultimo Target (gg)'] = (oggi_dt - analisi_target['Ultimo Target']).dt.days
        
        diff_date_target = (analisi_target['Ultimo Target'] - analisi_target['Primo Target']).dt.days
        analisi_target['Freq. Aiuti Target (gg)'] = diff_date_target / (analisi_target['N° Aiuti Target'] - 1)
        analisi_target['Freq. Aiuti Target (gg)'] = analisi_target['Freq. Aiuti Target (gg)'].replace([float('inf'), -float('inf')], pd.NA)

        # 3. Merge Finale
        analisi_finale = analisi_target.merge(analisi_tot[['CF_TROVATO', 'N° Aiuti Tot', 'Freq. Aiuti (gg)']], on='CF_TROVATO', how='left')
        analisi_finale['Quota %'] = (analisi_finale['N° Aiuti Target'] / analisi_finale['N° Aiuti Tot']) * 100
        analisi_finale['Aiuti Target (%)'] = analisi_finale.apply(lambda x: f"{int(x['N° Aiuti Target'])} ({x['Quota %']:.1f}%)", axis=1)
        analisi_finale.rename(columns={'CF_TROVATO': 'P.IVA'}, inplace=True)

        # --- 4. CALCOLO SOGLIE E VIVACITÀ ---
    
        # SOGLIE RECENCY (Per lo Stato in tabella)
        q1_t = analisi_finale['Ultimo Target (gg)'].quantile(0.25)
        med_t = analisi_finale['Ultimo Target (gg)'].median()
        q3_t = analisi_finale['Ultimo Target (gg)'].quantile(0.75)
      
        # SOGLIE FREQUENCY (Per lo Stato in tabella)
        q1_f = analisi_finale['Freq. Aiuti Target (gg)'].quantile(0.25)
        med_f = analisi_finale['Freq. Aiuti Target (gg)'].median()
        q3_f = analisi_finale['Freq. Aiuti Target (gg)'].quantile(0.75)
        max_f = analisi_finale['Freq. Aiuti Target (gg)'].max()

        def get_vivacita_target(row):
          n_aiuti = row['N° Aiuti Target']
          rec = row['Ultimo Target (gg)']
          
          # INATTIVE
          # Se non ha aiuti target o se l'ultimo è più vecchio del 75% delle altre aziende
          if n_aiuti == 0 or rec > q3_t:
              return "☠️ INATTIVA"

          # NUOVI PLAYER
          # Se ha un solo aiuto target ed è più recente del 25% delle altre aziende
          if n_aiuti_target == 1 and rec_target <= q1_t:
            return "🌱 NUOVO PLAYER"
      
          # 2. LOGICA PER AZIENDE ATTIVE (Recency <= Q3)
          if n_aiuti == 1:
              return "🌱 POTENZIALE (NUOVA)"
      
          # Per chi ha più di 1 aiuto, calcoliamo il "Ritmo"
          freq = row['Freq. Aiuti Target (gg)']
          # Il ritardo è il rapporto tra l'attesa attuale e la media storica
          ritardo = rec / freq if freq > 0 else 1
      
          # --- IL CUORE DELLA LOGICA ---
          
          # 🔥 IPERATTIVA: Deve essere RECENTE (Rec < Mediana) E VELOCE (Freq < Q1)
          # È l'azienda che vince spesso e ha vinto da poco.
          if rec <= med_t and freq <= q1_f:
              return "🔥 IPERATTIVA"
      
          # ✅ VIVA: È a ritmo. Non importa quanto vince, l'importante è che 
          # l'ultimo aiuto sia coerente con la sua media storica.
          if ritardo <= 1.2:
              return "✅ VIVA (A RITMO)"
      
          # ⚠️ DISINTERESSATA: È fuori ritmo. Sta aspettando da più tempo 
          # di quanto solitamente faccia tra un bando e l'altro.
          if ritardo > 1.2:
              return "⚠️ DISINTERESSATA"
      
          return "🌑 MORTA"

        analisi_finale['Vivacità Target'] = analisi_finale.apply(get_vivacita_target, axis=1)

        # --- 5. KPI ---
        st.write("")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Aiuti (Mediana)", f"{analisi_finale['N° Aiuti Tot'].median():.0f}")
        c2.metric("Aiuti Target (Mediana)", f"{analisi_finale['N° Aiuti Target'].median():.0f}")
        c3.metric("Freq. Aiuti (Mediana)", f"{analisi_finale['Freq. Aiuti (gg)'].median():.0f} gg")
        c4.metric("Freq. Aiuti (Mediana)", f"{med_t:.0f} gg") # Usiamo med_t

        # --- 6. GRAFICO CON FINESTRE COLORATE (VERSIONE DEFINITIVA) ---
        # Creiamo un dataframe specifico per il grafico per evitare conflitti
        df_grafico = analisi_finale.dropna(subset=['Freq. Aiuti (gg)', 'Freq. Aiuti Target (gg)']).copy()
        
        if not df_grafico.empty:
            # TRUCCO FONDAMENTALE: Trasformiamo le due colonne in una colonna "Valore" e una "Tipo"
            # Questo obbliga Plotly a creare due tracce Box Plot distinte e visibili
            df_long = df_grafico.melt(
                id_vars=['Ragione Sociale', 'Budget Target (€)', 'N° Aiuti Target', 'Vivacità Target', 'Ultimo Target (gg)'],
                value_vars=['Freq. Aiuti (gg)', 'Freq. Aiuti Target (gg)'],
                var_name='Tipo Frequenza',
                value_name='Giorni'
            )
        
            fig_combined = px.histogram(
                df_long, 
                x="Giorni", 
                color="Tipo Frequenza",  # Forza la creazione di due legende e due boxplot
                marginal="box", 
                nbins=50, 
                barmode='overlay',
                color_discrete_map={"Freq. Aiuti (gg)": "#1f77b4", "Freq. Aiuti Target (gg)": "#FF0000"},
                opacity=0.7, 
                height=800,
                hover_data={
                    "Ragione Sociale": True,          # customdata[0]
                    "Budget Target (€)": ":,.0f",     # customdata[1]
                    "N° Aiuti Target": True,          # customdata[2]
                    "Vivacità Target": True,          # customdata[3]
                    "Ultimo Target (gg)": True,       # customdata[4]
                    "Tipo Frequenza": False           # Escludiamo dai customdata se non serve
                }
            )
        
            # AGGIUNTA FINESTRE COLORATE (Resta uguale)
            fig_combined.add_vrect(x0=0, x1=q1_f, fillcolor="#2ecc71", opacity=0.3, layer="below", line_width=0)
            fig_combined.add_vrect(x0=q1_f, x1=med_f, fillcolor="#c8e6c9", opacity=0.5, layer="below", line_width=0)
            fig_combined.add_vrect(x0=med_f, x1=q3_f, fillcolor="#fff176", opacity=0.5, layer="below", line_width=0)
            fig_combined.add_vrect(x0=q3_f, x1=max_f, fillcolor="#ef5350", opacity=0.3, layer="below", line_width=0)
        
            # Etichette finestre
            finestre = [{"label": "IPER.", "x0": 0, "x1": q1_f}, {"label": "VIVA", "x0": q1_f, "x1": med_f},
                        {"label": "DIS.", "x0": med_f, "x1": q3_f}, {"label": "MORTA", "x0": q3_f, "x1": max_f}]
            for f in finestre:
                fig_combined.add_annotation(x=(f["x0"]+f["x1"])/2, y=1, yref="paper", text=f["label"], 
                                           showarrow=False, font=dict(size=12, color="grey", family="Arial Black"), yanchor="bottom")
        
            # APPLICAZIONE HOVER SU TUTTI I BOX
            fig_combined.update_traces(
                boxpoints='all', pointpos=0, jitter=0.5, marker=dict(size=4),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>" +
                    "<b>Budget Target:</b> %{customdata[1]} €<br>" +
                    "<b>N° Aiuti Target:</b> %{customdata[2]}<br>" +
                    "<b>Stato:</b> %{customdata[3]}<br>" +
                    "<b>Ultimo Aiuto Target:</b> %{customdata[4]} gg<br>" +
                    "<b>Freq. Aiuti Target:</b> %{x:.0f} gg<extra></extra>"
                ),
                selector=dict(type='box')
            )
        
            fig_combined.update_layout(
                yaxis=dict(domain=[0, 0.45]),      
                yaxis2=dict(domain=[0.55, 1]),     
                bargap=0.05, 
                boxgap=0.3,           # Spazio tra i boxplot delle due serie
                boxgroupgap=0.1,      # Spazio tra i box nello stesso gruppo
                xaxis_title="Frequenza Aiuti (gg)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_combined, use_container_width=True)

        # 7. TABELLA
        st.write("")
        st.write("")
        col_view = ['P.IVA', 'Ragione Sociale', 'Budget Target (€)', 'Aiuti Target (%)', 
                    'Freq. Aiuti (gg)', 'Freq. Aiuti Target (gg)', 'Ultimo Target (gg)', 'Vivacità Target']

        
        def style_vivacita(val):
            colori = {
                '🔥 IPERATTIVA': 'background-color: #2ecc71; color: white; font-weight: bold;',       # IPERATTIVA: Verde acceso
                '✅ VIVA': 'background-color: #c8e6c9; color: #2e7d32; font-weight: bold;',           # VIVA: Verde pallido (Salvia/Pastello)
                '⚠️ DISINTERESSATA': 'background-color: #fff176; color: #f57f17; font-weight: bold;', # DISINTERESSATA: Giallo
                '🌑 MORTA': 'background-color: #ef5350; color: white; font-weight: bold;',            # MORTA: Rosso
                '🌱 OCCASIONALE': 'color: #95a5a6; font-style: italic;'                               # OCCASIONALE: Grigio neutro
            }
            return colori.get(val, '')

        st.dataframe(
            analisi_finale[col_view].sort_values('Ultimo Target (gg)').style.format({
                'Budget Target (€)': '{:,.0f} €',
                'Freq. Aiuti (gg)': '{:.0f} gg',
                'Freq. Aiuti Target (gg)': '{:.0f} gg',
                'Ultimo Target (gg)': '{:.0f} gg'
            })
            .map(style_vivacita, subset=['Vivacità Target'])
            .background_gradient(cmap='RdYlGn_r', subset=['Ultimo Target (gg)']),
            use_container_width=True, hide_index=True
        )
