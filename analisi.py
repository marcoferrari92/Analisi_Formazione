import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

colors = ['#27ae60', '#e74c3c'] 
def create_centered_pie(values):
    fig = go.Figure(data=[go.Pie(
                values=values,
                hole=.4,
                marker_colors=['#27ae60', '#e74c3c'],
                textinfo='percent', 
                insidetextorientation='horizontal',
                hoverinfo='label+percent',
                direction='clockwise',
                rotation=0,
                domain={'x': [0, 0.4], 'y': [0, 1]}
    )])
    
    fig.update_layout(
                height=150,      
                margin=dict(t=0, b=0, l=0, r=0), 
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig


def analisi_incidenza(df_report):
    """
    Funzione per visualizzare l'istogramma dell'incidenza di volume
    e spiegare il significato dei dati.
    """
    st.subheader("📈 Analisi della Specializzazione: Incidenza Volume Target")
    
    # 1. Preparazione Dati (Solo aziende con incidenza > 0)
    df_attivi = df_report[df_report['INCIDENZA_VOL_%'] > 0].copy()
    
    if df_attivi.empty:
        st.warning("Nessun dato di incidenza disponibile per le aziende selezionate.")
        return

    # 2. Creazione Grafico
    fig = px.histogram(
        df_attivi, 
        x="INCIDENZA_VOL_%", 
        nbins=20,
        histnorm='percent',
        title="Distribuzione % dell'Incidenza (Solo aziende attive nel Target)",
        labels={'INCIDENZA_VOL_%': 'Incidenza Volume Target (%)', 'percent': 'Quota di Aziende (%)'},
        color_discrete_sequence=['#27ae60'],
        marginal="box" # Il boxplot sopra l'istogramma
    )

    fig.update_layout(
        bargap=0.1,
        xaxis_ticksuffix="%",
        yaxis_ticksuffix="%"
    )

    # 3. Layout Streamlit: Grafico a sinistra, Spiegazione a destra
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🔍 Cosa stiamo guardando?")
        
        media = df_attivi['INCIDENZA_VOL_%'].mean()
        mediana = df_attivi['INCIDENZA_VOL_%'].median()
        
        st.metric("Media Incidenza", f"{media:.1f}%")
        st.metric("Mediana Incidenza", f"{mediana:.1f}%")
        
        st.info(f"""
        **Interpretazione:**
        - **La Media ({media:.1f}%)**: Rappresenta il 'punto di equilibrio'. Se è molto più alta della mediana, significa che pochi 'campioni' stanno alzando la media di tutto il gruppo.
        - **La Mediana ({mediana:.1f}%)**: È il valore centrale. Ci dice che metà delle aziende attive investe meno del {mediana:.1f}% del proprio budget RNA in formazione.
        """)

    # 4. Approfondimento didattico
    with st.expander("💡 Guida alla lettura del grafico"):
        st.write("""
        L'**Incidenza Volume** misura quanto pesa la formazione sul totale degli aiuti ricevuti da un'azienda.
        
        * **Fascia 0-20% (Aziende Hardware-Centric):** Imprese che investono principalmente in macchinari e infrastrutture. La formazione è un complemento.
        * **Fascia 80-100% (Aziende Skills-Centric):** Imprese (spesso di servizi o consulenza) il cui unico sostentamento pubblico deriva dallo sviluppo delle competenze.
        * **Il Boxplot (riga sopra):** La 'scatola' mostra dove si concentra il 50% centrale del mercato. I puntini a destra sono i tuoi 'Top Spender' o specialisti.
        """)
