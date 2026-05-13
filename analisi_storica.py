
# ***********************
# ANALISI STORICA (CAGR)
# ***********************

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots 
import datetime

GUIDA_CAGR = r"""

#### ⏳ Analisi Storica del Settore Target

In questa sezione trovi l'*Analisi Storica del Settore Target* che confronta la crescita composta (CAGR) con l'andamento mediano degli aiuti alle aziende.
Usa quest'analisi per comprendere lo scenario in cui si stanno muovendo le aziende: crescita, contrazione, ecc.

#### 📈 Guida al CAGR (Compound Annual Growth Rate)

Il **CAGR** misura la crescita media annua del **Settore Target**, ipotizzando una progressione costante.

$$CAGR = \left( \frac{\text{Valore Finale}}{\text{Valore Iniziale}} \right)^{\frac{1}{n}} - 1$$

1.  **Anno Zero**: Tutti i calcoli partono dall'anno zero del dataset (es. 2020).
2.  **Primo Anno**: Nel primo anno dopo l'inizio ($n=1$), il CAGR coincide con la *crescita semplice:* 
$$CAGR =\left( \frac{\text{Valore Finale - Valore Iniziale}}{\text{Valore Iniziale}} \right)$$. 
3.  **Anni Successivi**: I valori si "ammorbidiscono" perché la crescita totale viene spalmata (composta) su più anni rispetto all'anno zero.

**Esempio:** Un CAGR del 10% su 3 anni significa che, partendo dal valore iniziale, il settore è cresciuto mediamente del 10% ogni anno per tre anni di fila.

💡 Usa il CAGR per capire se il **Settore Target** è un settore in crescita su cui ha senso investire!
"""

def story_analysis(df):

    st.write("")
    with st.popover("💡 Strategia"):
        st.info(GUIDA_CAGR)
    st.write("")
    
    
    anno_corrente = datetime.datetime.now().year

    # 1. Raggruppamento e Calcoli core
    df_temp = df.copy()
    df_temp = df_temp[df_temp['RNA_ELEMENTO_DI_AIUTO'] > 0].copy()
    df_temp['RNA_DATA_CONCESSIONE'] = pd.to_datetime(df_temp['RNA_DATA_CONCESSIONE'])
    df_temp['AnnoMonth'] = df_temp['RNA_DATA_CONCESSIONE'].dt.to_period('M').astype(str)
    df_temp['Anno'] = df_temp['RNA_DATA_CONCESSIONE'].dt.year
    df_temp['Mese_Num'] = df_temp['RNA_DATA_CONCESSIONE'].dt.month
    df_annual = df_temp.groupby('Anno').agg(
        Aiuti_Tot=('RNA_ELEMENTO_DI_AIUTO', 'count'),
        Aiuti_Target=('IS_TARGET', 'sum'),
        Vol_Tot=('RNA_ELEMENTO_DI_AIUTO', 'sum'),
        Vol_Target=('RNA_ELEMENTO_DI_AIUTO', lambda x: df_temp.loc[x.index, 'RNA_ELEMENTO_DI_AIUTO'][df_temp['IS_TARGET'] == 1].sum()),
        Aiuto_Mediano_Target=('RNA_ELEMENTO_DI_AIUTO', lambda x: df_temp.loc[x.index, 'RNA_ELEMENTO_DI_AIUTO'][df_temp['IS_TARGET'] == 1].median())
    ).reset_index().sort_values('Anno')

    # Riempi i NaN (es. se in un anno non ci sono aiuti target, la mediana è NaN)
    df_annual['Aiuto_Mediano_Target'] = df_annual['Aiuto_Mediano_Target'].fillna(0)


    # CALCOL CAGR
    def calc_cagr(current_val, start_val, current_year, start_year):
        n_anni = current_year - start_year
        if n_anni <= 0 or start_val <= 0 or current_val <= 0: return 0.0
        return (current_val / start_val) ** (1 / n_anni) - 1

    anno_start = df_annual['Anno'].min()
    prat_target_start = df_annual['Aiuti_Target'].iloc[0] 
    vol_target_start = df_annual['Vol_Target'].iloc[0]

    # Calcolo metriche strategiche
    df_annual['Aiuto_Medio_Target'] = df_annual['Aiuto_Mediano_Target'] # Ora contiene la mediana
    df_annual['Quota Target (%)'] = (df_annual['Aiuti_Target'] / df_annual['Aiuti_Tot'] * 100).fillna(0)
    df_annual['Quota Vol. Target (%)'] = (df_annual['Vol_Target'] / df_annual['Vol_Tot'] * 100).fillna(0)
    df_annual['CAGR Target'] = df_annual.apply(lambda x: calc_cagr(x['Aiuti_Target'], prat_target_start, x['Anno'], anno_start) * 100, axis=1)
    df_annual['CAGR Vol. Target'] = df_annual.apply(lambda x: calc_cagr(x['Vol_Target'], vol_target_start, x['Anno'], anno_start) * 100, axis=1)

    # Mascheramento anno in corso per i CAGR
    df_annual.loc[df_annual['Anno'] == anno_corrente, ['CAGR Target', 'CAGR Vol. Target']] = None

    # --- PARTE SUPERIORE: IL GRAFICO ---
    fig_strategy = make_subplots(specs=[[{"secondary_y": True}]])

    # Barre: Aiuto Medio
    fig_strategy.add_trace(
        go.Bar(
            x=df_annual['Anno'],
            y=df_annual['Aiuto_Medio_Target'],
            name="Aiuto Target Medio (€)",
            marker_color='rgba(52, 152, 219, 0.6)',
            hovertemplate="Anno %{x}<br>Aiuto Medio: € %{y:,.0f}<extra></extra>"
        ), secondary_y=False
    )

    # Linea: CAGR Volume (solo anni completi)
    df_cagr_plot = df_annual.dropna(subset=['CAGR Vol. Target'])
    fig_strategy.add_trace(
        go.Scatter(
            x=df_cagr_plot['Anno'],
            y=df_cagr_plot['CAGR Vol. Target'],
            name="CAGR Vol. Target (%)",
            line=dict(color='#2ecc71', width=4, shape='spline'),
            mode='lines+markers+text',
            text=[f"{v:.1f}%" if v != 0 else "" for v in df_cagr_plot['CAGR Vol. Target']],
            textposition="top center",
            hovertemplate="Anno %{x}<br>CAGR: %{y:.2f}%<extra></extra>"
        ), secondary_y=True
    )

    fig_strategy.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
        template="plotly_white",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    fig_strategy.update_yaxes(title_text="Aiuto Medio (€)", secondary_y=False, tickformat="€,.0f")
    fig_strategy.update_yaxes(title_text="CAGR (%)", secondary_y=True, ticksuffix="%")
    fig_strategy.update_xaxes(type='category')

    st.plotly_chart(fig_strategy, use_container_width=True)

    # --- TABELLA DETTAGLIATA ---

    # Formattazione per la visualizzazione tabella
    df_view = df_annual.sort_values('Anno', ascending=False).copy()
    df_view['Vol. Tot. (€)'] = df_view['Vol_Tot'].apply(lambda x: f"€ {x/1e6:.2f}M")
    df_view['Vol. Target (€)'] = df_view['Vol_Target'].apply(lambda x: f"€ {x/1e6:.2f}M")

    df_final = df_view[[
        'Anno', 'Aiuti_Tot', 'Aiuti_Target', 'Quota Target (%)', 'CAGR Target',
        'Vol. Tot. (€)', 'Vol. Target (€)', 'Quota Vol. Target (%)', 'CAGR Vol. Target'
    ]]

    df_final.columns = [
        'Anno', 'Aiuti Tot.', 'Aiuti Target', 'Quota Target (%)', 'CAGR Target',
        'Vol. Tot. (€)', 'Vol. Target (€)', 'Quota Vol. Target (%)', 'CAGR Vol. Target'
    ]

    def color_cagr(val):
        try:
            if val is None or pd.isna(val): return ''
            v = float(val)
            if v > 0.001: return 'color: #27ae60; font-weight: bold;'
            if v < -0.001: return 'color: #e74c3c; font-weight: bold;'
        except: pass
        return ''

    st_df = df_final.style.map(
        color_cagr, subset=['CAGR Target', 'CAGR Vol. Target']
    ).format({
        'CAGR Target': "{:.2f} %", 'CAGR Vol. Target': "{:.2f} %",
        'Quota Target (%)': "{:.2f} %", 'Quota Vol. Target (%)': "{:.2f} %"
    }, na_rep="In corso...")

    st.write("")
    st.write("")
    st.dataframe(st_df, hide_index=True, use_container_width=True)

    
    # --- INTERPRETAZIONE FINALE INTEGRALE (16 SCENARI PIATTI) ---
    if len(df_annual) >= 2:
      
        df_valid = df_annual.dropna(subset=['CAGR Vol. Target'])
        ultimo = df_valid.iloc[-1]
        penultimo = df_valid.iloc[-2]
        
        # Variabili Decisionali
        cagr_att = ultimo['CAGR Vol. Target']
        c_pre = penultimo['CAGR Vol. Target']
        diff_cagr = cagr_att - c_pre
        diff_aiuto = ultimo['Aiuto_Medio_Target'] - penultimo['Aiuto_Medio_Target']
        diff_n = int(ultimo['Aiuti_Target'] - penultimo['Aiuti_Target'])
        
        # Dati pronti per le f-string
        anno_u = int(ultimo['Anno'])
        anno_p = int(penultimo['Anno'])
        a_med = ultimo['Aiuto_Medio_Target']
        
        # Calcolo quote percentuali
        p_aiuto = (diff_aiuto / penultimo['Aiuto_Medio_Target'] * 100) if penultimo['Aiuto_Medio_Target'] > 0 else 0
        p_n = (diff_n / penultimo['Aiuti_Target'] * 100) if penultimo['Aiuti_Target'] > 0 else 0

        st.write("")

        # --- AREA 1: CAGR POSITIVO + ACCELERAZIONE ---

        if cagr_att > 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n > 0:
            st.success("🚀 **BOOM TOTALE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante l'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target è in piena espansione: aumentano contemporaneamente il numero di progetti e il loro valore economico.
            """)

        elif cagr_att > 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n <= 0:
            st.success("🚀 **ACCELERAZIONE E VALORE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Grazie al calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target è in accelerazione e sta puntando su meno aiuti prioritari dal peso maggiore.
            """)

        elif cagr_att > 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n > 0:
            st.success("🚀 **ACCELERAZIONE E DIFFUSIONE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è diminuito di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target è in accelerazione e sta puntando sulla capillarità: fornendo più aiuti ma dal peso minore.
            """)

        elif cagr_att > 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.warning("⚠️ **ANOMALIA STATISTICA (INERZIA STORICA)**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta accelerando al CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il trend storico accelera per inerzia, ma l'anno corrente segna una contrazione reale su tutti i fronti. Verificare la saturazione del mercato.
            """)

        # --- AREA 2: CAGR POSITIVO + RALLENTAMENTO ---

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n > 0:
            st.warning("⚠️ **ANOMALIA DI TREND (INERZIA STORICA)**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** mostra un CAGR in rallentamento al **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante l'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Caso di inerzia statistica: i dati correnti (sia numero di aiuti che valore medio in crescita) indicano un mercato in salute, ma il CAGR rallenta perché confrontato con picchi storici passati eccezionali.
            """)

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n <= 0:
            st.info("📉 **RALLENTAMENTO CON CONSOLIDAMENTO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** continua a crescere al CAGR del **{cagr_att:.1f}%** ma **📉 in rallentamento** rispetto al {anno_p} ({c_pre:.1f}%).
            * Grazie al calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Dopo un'annata d'oro, il mercato target sta rallentando, spostando il baricentro su meno progetti ma più corposi.
            """)

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n > 0:
            st.info("📉 **RALLENTAMENTO CON FRAZIONAMENTO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** continua a crescere al CAGR del **{cagr_att:.1f}%** ma **📉 in rallentamento** rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Dopo un'annata d'oro, il mercato target sta rallentando puntando a fornire più aiuti ma meno corposi.
            """)

        elif cagr_att > 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.info("📉 **AVVISO DI CONTRAZIONE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** continua a crescere al CAGR del **{cagr_att:.1f}%** ma **📉 in rallentamento** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Fase di contrazione: il rallentamento del mercato target è accompagnato da un calo sia nel numero di aiuti che nel loro valore medio.
            """)

        # --- AREA 3: CAGR NEGATIVO + RECUPERO ---

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n > 0:
            st.warning("⚠️ **RECUPERO SISTEMICO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte di un aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Segnali di ripresa: il mercato ricomincia ad aggiungere più aiuti e a maggior capitale.
            """)

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto > 0 and diff_n <= 0:
            st.warning("⚠️ **RECUPERO QUALITATIVO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * Grazie al calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il calo del mercato si attenua grazie a progetti più grandi che tengono in piedi il settore nonostante la perdita di molti aiuti.
            """)

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n > 0:
            st.warning("⚠️ **RECUPERO QUANTITATIVO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato sta cercando di risollevararsi aumentando il numero di concessioni a basso costo per stimolare il settore.
            """)

        elif cagr_att <= 0 and diff_cagr > 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.warning("⚠️ **RIMBALZO TECNICO**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** cala (**{cagr_att:.1f}%**) ma recupera rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il calo è meno severo, ma non ci sono spinte reali né nel valore medio né nel numero di aiuti.
            """)

        # --- AREA 4: CAGR NEGATIVO + AGGRAVAMENTO ---

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n > 0:
            st.error("🚨 **DISPERSIONE E CRISI**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante un aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è comunque salito di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Caso critico: nonostante aumentino aiuti e loro capitale il mercato target sta crollando drasticamente.
            """)

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto > 0 and diff_n <= 0:
            st.error("🚨 **EROSIONE SELETTIVA**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Al calo di {abs(diff_n)} aiuti ({p_n:.1f}%) è seguito l'aumento dell'**Aiuto Medio** di **€ {diff_aiuto:,.0f}** ({p_aiuto:+.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target sta crollando e sopravvivono solo pochi progetti grandi, mentre la base del mercato sta scomparendo del tutto.
            """)

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n > 0:
            st.error("🚨 **POLVERIZZAZIONE DA CRISI**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * A fronte dell'aumento di {diff_n} aiuti ({p_n:+.1f}%), l'**Aiuto Medio** è sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Il mercato target si sta polverizzando in piccoli aiuti che non sostengono il volume economico del settore.
            """)

        elif cagr_att <= 0 and diff_cagr <= 0 and diff_aiuto <= 0 and diff_n <= 0:
            st.error("🚨 **RECESSIONE TOTALE**")
            st.markdown(f"""
            **Nell'anno {anno_u}:**
            * Il volume del **Settore Target** sta crollando a un tasso CAGR del **{cagr_att:.1f}%** rispetto al {anno_p} ({c_pre:.1f}%).
            * Nonostante il calo di {abs(diff_n)} aiuti ({p_n:.1f}%), l'**Aiuto Medio** è comunque sceso di **€ {abs(diff_aiuto):,.0f}** ({p_aiuto:.1f}%) arrivando a **€ {a_med:,.0f}**.
            * **Significato:** Stato di crisi massima: esaurimento dei fondi e crollo totale dell'interesse e del valore sul mercato target.
            """)
