



def analisi_benchmark(df_plot, med_Fo, med_Fe, custom_data, custom_template):
    """
    Gestisce il rendering della sezione dedicata agli outlier, 
    inclusi i grafici 2D e il cubo 3D del Market Power.
    """
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
            is_log=False        
        )
        st.plotly_chart(fig_op, use_container_width=True)
        if med_Fo > 0:
            st.caption(f"La linea rossa rappresenta la Mediana Fo ({med_Fo:.1f}%). Dimensione: Budget Target.")
        
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
            is_log=True         
        )
        st.plotly_chart(fig_ec, use_container_width=True)
        if med_Fe > 0:
            st.caption(f"La linea blu rappresenta la Mediana Fe ({med_Fe:.1f}%). Dimensione: Num. Aiuti Target.")

    # --- 2. GRAFICO CONFRONTO TARGET ---
    st.write("")
    fig_vs = plot_scatter_median(
            df=df_plot, 
            x_col="Budget Target", 
            y_col="Aiuti Target", 
            color_col="Fe",
            title="Confronto Specializzazioni (Num. Aiuti Target vs Budget Target)", 
            med_val=med_Fe, 
            custom_data=custom_data, 
            size_col="Budget",
            hover_template=custom_template, 
            line_color="Blue", 
            is_log=True         
    )
    st.plotly_chart(fig_vs, use_container_width=True)
    st.caption("Dimensione del pallino: Budget Totale dell'azienda.")

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
