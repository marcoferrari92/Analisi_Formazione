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



def plot_scatter_median(df, x_col, y_col, color_col, title, med_val, custom_data, hover_template, line_color="Red", is_log=False):
    """
    Crea un grafico scatter 2D avanzato con linea di benchmark e tooltip personalizzato.

    Args:
        df (pd.DataFrame):              Il DataFrame contenente i dati delle aziende.
        x_col (str):                    Nome colonna per l'asse X (es. 'Aiuti' o 'Budget').
        y_col (str):                    Nome colonna per l'asse Y (es. 'Aiuti Target' o 'Budget Target').
        color_col (str):                Colonna per la scala cromatica dei punti (es. 'Fo' o 'Fe').
        title (str):                    Titolo del grafico.
        med_val (float):                Valore della mediana (0-100) per inclinazione linea di benchmark.
        custom_data (list):             Lista delle colonne da mappare per l'uso nel hover_template.
        hover_template (str):           Stringa di formattazione HTML per il tooltip di Plotly.
        line_color (str, optional):     Colore della linea tratteggiata. Default "Red".
        is_log (bool, optional):        Attiva la scala logaritmica su entrambi gli assi. Default False.

    Returns:
        plotly.graph_objects.Figure:    Oggetto figura di Plotly pronto per st.plotly_chart.
    """
    
    # 1. Creazione Scatter base
    # La scala colori cambia (Viridis/Plasma) per distinguere grafici logaritmici da lineari
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col,
        hover_name="Ragione Sociale",
        custom_data=custom_data,
        title=title,
        log_x=is_log, log_y=is_log,
        color_continuous_scale="Viridis" if is_log else "Plasma"
    )

    # 2. Iniezione del template personalizzato per il tooltip
    fig.update_traces(hovertemplate=hover_template)

    # 3. Logica della Linea di Benchmark (Bisettrice della Mediana)
    # Viene disegnata solo se esiste una mediana valida (> 0)
    if med_val > 0:
        x_min, x_max = df[x_col].min(), df[x_col].max()
        
        # Disegna una retta passante per l'origine con pendenza = mediana%
        fig.add_shape(
            type="line",
            x0=x_min, y0=x_min * (med_val / 100),
            x1=x_max, y1=x_max * (med_val / 100),
            line=dict(color=line_color, width=3, dash="dash")
        )

    # 4. Pulizia estetica del layout
    fig.update_layout(height=450, showlegend=False)
    
    return fig

