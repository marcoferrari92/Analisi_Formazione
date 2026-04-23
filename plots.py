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



def plot_scatter_median(df, x_col, y_col, color_col, title, med_val, custom_data, hover_template, size_col=None, line_color="Red", is_log=False):
    """
    Crea un grafico scatter 2D con dimensione dei punti variabile e linea di benchmark.

    Args:
        df (pd.DataFrame):      Il DataFrame contenente i dati.
        x_col (str):            Colonna asse X.
        y_col (str):            Colonna asse Y.
        color_col (str):        Colonna per il colore (es. 'Aiuti Target').
        size_col (str):         Colonna per la dimensione del pallino (es. 'Budget Target').
        title (str):            Titolo del grafico.
        med_val (float):        Valore mediana per la linea di benchmark.
        custom_data (list):     Colonne per il tooltip.
        hover_template (str):   Template HTML per il tooltip.
        line_color (str):       Colore linea benchmark. Default "Red".
        is_log (bool):          Scala logaritmica. Default False.
    """
    
    # 1. Creazione Scatter
    fig = px.scatter(
        df, 
        x=x_col, 
        y=y_col, 
        color=color_col,
        size=size_col,          # Se size_col è None, Plotly usa la dimensione standard
        hover_name="Ragione Sociale",
        custom_data=custom_data,
        title=title,
        log_x=is_log, 
        log_y=is_log,
        color_continuous_scale="Viridis" if is_log else "Plasma",
        # Usiamo size_max solo se effettivamente passiamo una colonna per la dimensione
        size_max=30 if size_col is not None else None 
    )

    # 2. Iniezione del template
    fig.update_traces(hovertemplate=hover_template)
    
    # Se non c'è una colonna size, impostiamo una dimensione fissa gradevole per tutti
    if size_col is None:
        fig.update_traces(marker=dict(size=10))

    # 3. Logica della Linea di Benchmark
    if med_val > 0:
        x_min, x_max = df[x_col].min(), df[x_col].max()
        fig.add_shape(
            type="line",
            x0=x_min, y0=x_min * (med_val / 100),
            x1=x_max, y1=x_max * (med_val / 100),
            line=dict(color=line_color, width=3, dash="dash")
        )

    fig.update_layout(height=450, showlegend=True if size_col else False)
    
    return fig

