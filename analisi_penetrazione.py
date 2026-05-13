import pandas as pd
import plotly.express as px
import streamlit as st

GUIDA = r"""
Carica il database clienti per verificare quanto sei penetrato nel Settore Target
"""

def penetration_analysis(df):

        n_aziende        = len(set(df['RNA_CODICE_FISCALE_BENEFICIARIO'].unique()))
        n_aziende_target = len(set(df[df['IS_TARGET'] == 1]['RNA_CODICE_FISCALE_BENEFICIARIO'].unique()))
        
        # Calcolo aziende clienti nel target
        if 'STATO' in df.columns:
            # Contiamo i CF univoci che sono sia in target che già clienti
            val_clienti = df[
                (df['IS_TARGET'] == 1) & 
                (df['STATO'].str.contains('MATCH', case=False, na=False))
            ]['RNA_CODICE_FISCALE_BENEFICIARIO'].nunique()
        else:
            val_clienti = 0

        # Creazione del DataFrame per il grafico
        funnel_df = pd.DataFrame({
            "Fase": ["Aziende Totali", "Aziende Target", "Aziende Clienti"],
            "Numero": [n_aziende, n_aziende_target, val_clienti]
        })

        # Generazione del Grafico
        fig_funnel = px.funnel(
            funnel_df, 
            x='Numero', 
            y='Fase',
            title="Penetrazione Settore Target",
            color_discrete_sequence=["#3498db"]
        )
        fig_funnel.update_traces(textinfo="value+percent initial")
        fig_funnel.update_layout(
            height=450, 
            margin=dict(t=50, b=0, l=10, r=10),
            template="plotly_white"
        )
        st.plotly_chart(fig_funnel, use_container_width=True, key="funnel_qualificazione_leads")

  
