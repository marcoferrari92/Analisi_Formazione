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


def crea_scatter_posizionamento(df, x_col, y_col, color_col, title, med_val, line_color="Red", is_log=False):
    """
    Crea un grafico scatter 2D con hover personalizzato e linea di benchmark (mediana) colorabile.
    """
    # 1. Definizione colonne per l'hover
    custom_data_cols = ['Aiuti', 'Aiuti Target', 'Fo', 'Budget', 'Budget Target', 'Fe']
    
    # 2. Creazione Scatter
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col,
        hover_name="Ragione Sociale",
        custom_data=custom_data_cols,
        title=title,
        log_x=is_log, log_y=is_log,
        color_continuous_scale="Viridis" if is_log else "Plasma"
    )

    # 3. Applicazione Hover Template Universale
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>" +
            "------------------<br>" +
            "Aiuti: %{customdata[0]}<br>" +
            "Aiuti Target: %{customdata[1]}<br>" +
            "Fattore Fo: %{customdata[2]:.1f}%<br>" +
            "Budget Totale: €%{customdata[3]:,.0f}<br>" +
            "Budget Target: €%{customdata[4]:,.0f}<br>" +
            "Fattore Fe: %{customdata[5]:.1f}%<br>" +
            "<extra></extra>"
        )
    )

    # 4. Aggiunta Linea di Benchmark con colore personalizzato
    x_min, x_max = df[x_col].min(), df[x_col].max()
    fig.add_shape(
        type="line",
        x0=x_min, y0=x_min * (med_val / 100),
        x1=x_max, y1=x_max * (med_val / 100),
        line=dict(color=line_color, width=3, dash="dash") # <-- Colore dinamico qui
    )

    fig.update_layout(height=450, showlegend=False)
    return fig


