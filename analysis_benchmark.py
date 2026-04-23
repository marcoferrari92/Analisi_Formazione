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
