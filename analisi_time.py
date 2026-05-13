import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots 
import datetime as dt
import plotly.figure_factory as ff


GUIDA_TIMELINE = """ Vedi se il settore target è in crescita, in declino o se ha un andamento periodico legato a bandi stagionali"""
GUIDA_TIMEMAP = """ Periodi che si ripetono come i più intensi (vincitori) in più annate, e che hanno anche un budget medio annuo più alto, potrebbero indicare un trend nell'ingresso di liquidità delle aziendeda per il settore target. 
                    Potrebbe essere utile attivare le campagne marketing nei mesi subiti precedenti"""
GUIDA_CAGR = r"""
#### 📈 Guida al CAGR (Compound Annual Growth Rate)

Il **CAGR** misura la crescita media annua del **Settore Target**, ipotizzando una progressione costante.

$$CAGR = \left( \frac{\text{Valore Finale}}{\text{Valore Iniziale}} \right)^{\frac{1}{n}} - 1$$

1.  **Anno Zero**: Tutti i calcoli partono dal primo anno del dataset (es. 2020).
2.  **Primo Anno**: Nel primo anno dopo l'inizio ($n=1$), il CAGR coincide con la *crescita semplice*. 
3.  **Anni Successivi**: I valori si "ammorbidiscono" perché la crescita totale viene spalmata (composta) su più anni rispetto all'anno zero.

**Esempio:** Un CAGR del 10% su 3 anni significa che, partendo dal valore iniziale, il settore è cresciuto mediamente del 10% ogni anno per tre anni di fila.

💡 Usa il CAGR per capire se il **Settore Target** è un settore in crescita su cui ha senso investire!
"""



def time_analysis(df):
    """
    Renderizza l'analisi temporale con grafici a linee perfettamente sincronizzati
    e collegati da una Spike Line verticale unica (hover unificato).
    """
    # --- 1. Preparazione Dati Locale (Invariata) ---
    df_temp = df.copy()
    df_temp = df_temp[df_temp['RNA_ELEMENTO_DI_AIUTO'] > 0].copy()
    df_temp['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_temp['RNA_DATA_CONCESSIONE'])
    df_temp['AnnoMonth'] = df_temp['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
    df_temp['Anno'] = df_temp['RNA_DATA_CONCESSIONE'].dt.year
    df_temp['Mese_Num'] = df_temp['RNA_DATA_CONCESSIONE'].dt.month
    
    # Aggregazione
    df_time_tot = df_temp.groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    df_time_targ = df_temp[df_temp['IS_TARGET'] == 1].groupby('AnnoMonth')['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    
    df_time_plot = pd.merge(df_time_tot, df_time_targ, on='AnnoMonth', how='left', suffixes=('_Tot', '_Targ')).fillna(0)
    df_time_plot.columns = ['Periodo', 'Mercato Totale', 'Settore Target']
    
    # Calcoli per i grafici
    df_time_plot['Quota Target (%)'] = (df_time_plot['Settore Target'] / df_time_plot['Mercato Totale'] * 100).fillna(0)
    df_time_plot['Mercato_Mln'] = df_time_plot['Mercato Totale'] / 1e6
    df_time_plot['Target_Mln'] = df_time_plot['Settore Target'] / 1e6

    # Range per sincronizzare perfettamente l'asse X (Invariato)
    x_min = df_time_plot['Periodo'].min()
    x_max = df_time_plot['Periodo'].max()

    # --- INIZIO COSTRUZIONE FIGURA UNICA ---
    st.write("")
    with st.popover("💡 Strategia"):
        st.info(GUIDA_TIMELINE)
    
    # 2. Creazione della Figura con Subplots (2 righe, 1 colonna)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08, # Spazio tra i due grafici
        subplot_titles=("Quota di Mercato del Settore Target", "Evoluzione Temporale del Budget (Mln €)")
    )
    # Quota Target (%) - Area chart
    fig.add_trace(
        go.Scatter(
            x=df_time_plot['Periodo'], 
            y=df_time_plot['Quota Target (%)'],
            name="Quota Target (%)",
            line=dict(color='#e74c3c', width=2, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.2)', 
            mode='lines+markers',
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    # Mercato Totale (Mln €) - Linea Blu
    fig.add_trace(
        go.Scatter(
            x=df_time_plot['Periodo'], 
            y=np.sqrt(df_time_plot['Mercato_Mln']),
            name="Mercato Totale",
            line=dict(color='#3498db', width=2, shape='spline'),
            mode='lines+markers',
            marker=dict(size=6),
            hovertemplate="Mercato Totale: %{text:.2f} Mln €<extra></extra>",
            text=df_time_plot['Mercato_Mln']
        ),
        row=2, col=1
    )
    
    # Settore Target (Mln €) - Linea Rossa
    fig.add_trace(
        go.Scatter(
            x=df_time_plot['Periodo'], 
            y=np.sqrt(df_time_plot['Target_Mln']),
            name="Settore Target",
            line=dict(color='#e74c3c', width=2, shape='spline'),
            mode='lines+markers',
            marker=dict(size=6),
            hovertemplate="Settore Target: %{text:.2f} Mln €<extra></extra>",
            text=df_time_plot['Target_Mln']
        ),
        row=2, col=1
    )

    # --- C. CONFIGURAZIONE LAYOUT E ASSI ---
    # Calcolo Tick asse Y inferiore (Scala Radice Quadrata)
    max_mln = df_time_plot['Mercato_Mln'].max()
    potential_ticks = np.array([0, 1, 5, 10, 25, 50, 100, 200, 400, 800])
    tick_vals = potential_ticks[potential_ticks <= max_mln]
    if max_mln not in tick_vals: tick_vals = np.append(tick_vals, max_mln)

    fig.update_layout(
        template="plotly_white",
        height=700, 
        margin=dict(l=80, r=40, t=50, b=50), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        xaxis=dict(
            showspikes=True,
            spikemode='across+marker',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#999999'
        )
    )
    fig.update_yaxes(
        title_text="Quota Target (%)", 
        ticksuffix="%", 
        gridcolor="#f0f0f0", 
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Budget (Mln €)", 
        tickmode='array',
        tickvals=np.sqrt(tick_vals),
        ticktext=[f"{v:.1f}" for v in tick_vals],
        gridcolor="#f0f0f0",
        row=2, col=1
    )
    fig.update_xaxes(
        range=[x_min, x_max], 
        constrain='domain', 
        gridcolor="#e1e1e1", 
        griddash="dot", 
        row=1, col=1
    )
    fig.update_xaxes(
        title_text="Periodo", 
        range=[x_min, x_max], 
        constrain='domain', 
        gridcolor="#e1e1e1", 
        griddash="dot", 
        row=2, col=1
    )
    st.plotly_chart(fig, use_container_width=True, key="temporal_subplots")
    

  
    # *******************
    # HEATMAP STAGIONALE 
    # *******************
  
    st.divider()
    st.write("")
    st.subheader("🔥 Intensità degli Aiuti Target per Mese e Anno")
    st.write("")
              
    df_heat_data = df_temp[df_temp['IS_TARGET'] == 1].groupby(['Anno', 'Mese_Num'])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
    pivot_heat = df_heat_data.pivot(index='Anno', columns='Mese_Num', values='RNA_ELEMENTO_DI_AIUTO').fillna(0)
    pivot_heat = pivot_heat.sort_index(ascending=False)
    
    mesi_ita = {1:'Gen', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mag', 6:'Giu', 7:'Lug', 8:'Ago', 9:'Set', 10:'Ott', 11:'Nov', 12:'Dic'}
    pivot_heat.columns = [mesi_ita.get(c, c) for c in pivot_heat.columns]
    
    fig_heat = px.imshow(
        pivot_heat,
        labels=dict(x="Mese", y="Anno", color="Budget (€)"),
        x=pivot_heat.columns,
        y=[str(a) for a in pivot_heat.index],
        color_continuous_scale="Reds",
        text_auto=".2s"
    )
    
    fig_heat.update_layout(
        coloraxis_colorbar_title_text="",
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(type='category', autorange="reversed")
    )
    
    st.plotly_chart(fig_heat, use_container_width=True, key="heatmap_stagionalita")

    # --- ANALISI DINAMICA DELLE FINESTRE TEMPORALI ---
    # Layout
    col0, col1, col2, col3, col4 = st.columns([0.3, 1.3, 0.3, 2.3, 0.3])

    anno_attuale = dt.datetime.now().year
    df_clean = df_temp[(df_temp['IS_TARGET'] == 1) & (df_temp['Anno'] < anno_attuale)].copy()
    
    if not df_clean.empty:
        with col1:
            window_size = st.slider("Ampiezza finestra (mesi):", min_value=1, max_value=12, value=4, key="slider_vincitori")
            with st.popover("💡 Strategia"):
              st.info(GUIDA_TIMEMAP)
      
        # Logica di calcolo (identica alla precedente)
        df_m_y = df_clean.groupby(['Anno', 'Mese_Num'])['RNA_ELEMENTO_DI_AIUTO'].sum().reset_index()
        budget_totale_storico = df_clean['RNA_ELEMENTO_DI_AIUTO'].sum()
          
        rolling_data = []
        for i in range(1, 13):
            mesi_w = []
            nomi_mesi_w = []
            for offset in range(window_size):
                m = i + offset
                if m > 12: m -= 12
                mesi_w.append(m)
                nomi_mesi_w.append(mesi_ita[m])
            
            nome_w = nomi_mesi_w[0] if window_size == 1 else f"{nomi_mesi_w[0]}-{nomi_mesi_w[-1]}"
            for anno in df_m_y['Anno'].unique():
                valore = df_m_y[(df_m_y['Anno'] == anno) & (df_m_y['Mese_Num'].isin(mesi_w))]['RNA_ELEMENTO_DI_AIUTO'].sum()
                rolling_data.append({'Anno': int(anno), 'Finestra': nome_w, 'Budget': valore})

        df_rolling_all = pd.DataFrame(rolling_data)

        # Metriche e Vincitori
        stats_w = df_rolling_all.groupby('Finestra')['Budget'].agg(['mean', 'sum']).reset_index()
        stats_w.columns = ['Finestra', 'Budget Medio (€)', 'Somma Totale']
        stats_w['Quota sul Totale %'] = (stats_w['Somma Totale'] / budget_totale_storico) * 100

        idx_max = df_rolling_all.groupby('Anno')['Budget'].idxmax()
        vincitori_annuali = df_rolling_all.loc[idx_max]
        
        vittorie = vincitori_annuali['Finestra'].value_counts().reset_index()
        vittorie.columns = ['Finestra', 'Vittorie']
        
        anni_vittoria = vincitori_annuali.groupby('Finestra')['Anno'].apply(lambda x: ', '.join(map(str, sorted(x, reverse=True)))).reset_index()
        anni_vittoria.columns = ['Finestra', 'Anni Vittoria']

        # Unione e FILTRO CRUCIALE
        classifica_finale = stats_w.merge(vittorie, on='Finestra', how='inner') # 'inner' tiene solo chi ha vinto
        classifica_finale = classifica_finale.merge(anni_vittoria, on='Finestra', how='left')
        
        classifica_finale = classifica_finale.sort_values(['Vittorie', 'Budget Medio (€)'], ascending=False)

        with col3:
            if not classifica_finale.empty:
                st.write(f"**Periodi Hot (Finestre di {window_size} mesi)**")
                st.dataframe(
                    classifica_finale[['Finestra', 'Vittorie', 'Anni Vittoria', 'Budget Medio (€)', 'Quota sul Totale %']].style.format({
                        'Budget Medio (€)': '{:,.0f} €',
                        'Quota sul Totale %': '{:.2f} %'
                    }).background_gradient(cmap='YlOrRd', subset=['Quota sul Totale %', 'Vittorie']),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.error("Nessuna finestra ha vinto in modo chiaro. Prova a cambiare l'ampiezza dello slider.")

    else:
        st.warning("Dati insufficienti negli anni conclusi.")
