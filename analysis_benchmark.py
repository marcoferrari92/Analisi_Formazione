import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def grafici_posizionamento(df_plot, med_Fo, med_Fe, custom_data, custom_template):
    
    from plots import plot_scatter_median
    
    if df_plot.empty:
        st.warning("Nessun dato disponibile per l'analisi degli outlier.")
        return

    st.write("")

    
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
        med_val=0, # Disattiviamo la linea diagonale
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

    c1, c2 = st.columns(2)
    with c1:
        st.success("**Top-Right (I Campioni)**: Alta specializzazione e alto valore. Lead prioritari.")
        st.warning("**Bottom-Right (Gli Specialisti)**: Alta frequenza target, ma piccoli importi.")
    with c2:
        st.info("**Top-Left (I Giganti)**: Grandi importi target, ma dispersi in molta altra attività.")
        st.error("**Bottom-Left (Gli Occasionali)**: Basso interesse strategico.")

    
    # --- 3. GRAFICO 3D: MARKET POWER ---
    st.write("")
    st.subheader("🧊 Cubo del Market Power: Massa vs Frequenza")
    
    with st.expander("📖 Come leggere i piani di benchmark"):
        st.info("""
        In questo spazio 3D, le aziende "normali" volano vicino ai due piani. Gli outlier scappano verso l'alto:
        * **Sopra il Piano Blu (Fe):** Aziende che ottengono più budget target rispetto alla loro massa monetaria totale.
        * **Sopra il Piano Rosso (Fo):** Aziende che vincono più bandi target rispetto al volume totale di pratiche.
        """)
    
    # Calcoli per il 3D
    ticket_target_med = (df_plot['Budget Target'] / df_plot['Aiuti Target']).median()
    x_range = np.logspace(np.log10(df_plot['Budget'].min()), np.log10(df_plot['Budget'].max()), 2)
    y_range = np.linspace(df_plot['Aiuti'].min(), df_plot['Aiuti'].max(), 2)
    g_x, g_y = np.meshgrid(x_range, y_range)
    
    z_fe = g_x * (med_Fe / 100)
    z_fo = g_y * (med_Fo / 100) * ticket_target_med
    
    fig_power = go.Figure()
    
    size_val = np.sqrt(df_plot['Budget Target'])
    size_val = (size_val / size_val.max()) * 30 + 5
    
    fig_power.add_trace(go.Scatter3d(
        x=df_plot['Budget'], y=df_plot['Aiuti'], z=df_plot['Budget Target'],
        mode='markers',
        hovertext=df_plot['Ragione Sociale'],
        customdata=df_plot[custom_data],
        marker=dict(
            size=size_val,
            color=df_plot['Aiuti Target'],
            colorscale='Viridis',
            opacity=0.7,
            showscale=True,
            colorbar=dict(title="N. Aiuti Target", thickness=15)
        ),
        hovertemplate=custom_template
    ))
    
    fig_power.add_trace(go.Surface(
        x=g_x, y=g_y, z=z_fe,
        opacity=0.15, showscale=False, colorscale=[[0, 'blue'], [1, 'blue']],
        name="Benchmark Economico (Fe)"
    ))
    
    fig_power.add_trace(go.Surface(
        x=g_x, y=g_y, z=z_fo,
        opacity=0.15, showscale=False, colorscale=[[0, 'red'], [1, 'red']],
        name="Benchmark Operativo (Fo)"
    ))
    
    fig_power.update_layout(
        scene=dict(
            xaxis_title="Budget Totale (€)",
            yaxis_title="N. Aiuti Totali",
            zaxis_title="Budget Target (€)",
            xaxis_type="log",
            zaxis_type="log"
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=800
    )
    
    st.plotly_chart(fig_power, use_container_width=True, key="market_power_cube_3d")
