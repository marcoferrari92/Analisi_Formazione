# settings.py

# Colonne del database RNA su cui effettuare la ricerca delle keyword
COLONNE_RICERCA = [
    'RNA_TITOLO_MISURA', 
    'RNA_DESCRIZIONE_PROGETTO', 
    'RNA_TITOLO_PROGETTO'
]

# Keyword predefinite che appariranno all'avvio dell'app
DEFAULT_KEYWORDS = "formazione, competenze, corso, training, innovazione"

# Eventuali altre impostazioni (es. colori o parametri CSV)
CSV_SEP = ';'
CSV_ENCODING = 'utf-8-sig'


GUIDA_TIMELINE = """ Vedi se il settore target è in crescita, in declino o se ha un andamento periodico legato a bandi stagionali"""
GUIDA_TIMEMAP = """I mesi più intensi indicano quando le aziende ricevono più liquidità. Individua i momenti migliori per proporre nuovi investimenti"""
        

GUIDA_PARETO = """
Questo grafico utilizza la **Regola di Pareto (80/20)** per analizzare quanto è "oligarchico" il tuo settore target:

1.  **Barre Blu**: Budget di aiuti ottenuto da ogni singola azienda nel settore target. Ordinate dalla maggiore alla minore.
2.  **Linea Rossa**: È la "Percentuale Cumulata". Sale man mano che sommiamo i budget delle aziende fino a intersecare la soglia dell'80%.
3.  **Intersezione**: La linea tratteggiata verticale indica quante aziende controllano l'80% dei fondi totali del settore.

**Cosa significa per te?**
* **Retta verticale molto a sinistra:** Il mercato è concentrato. Ti basta acquisire pochi "Big Client" per dominare il settore, ma la competizione sarà maggiore. 
* **Retta verticale molto a destra:** Il tuo pacchetto prospetti è frammentato. La strategia vincente è il volume e la capillarità commerciale.
"""


GUIDA_BENCHMARK = """
Il benchmark permette di confrontare la singola azienda con la **"linea di mezzo (mediana)"** del mercato di riferimento. 

### 📊 Mediana
A differenza della media (che può essere influenzata da pochi valori estremi - **outlier** - come un'azienda che riceve milioni di euro), la **Mediana** è il valore che divide esattamente in due la popolazione: il 50% delle aziende si trova sopra questo valore e il 50% sotto. 
Rappresenta quindi l'**azienda tipica** del settore: se un'azienda è sotto la mediana, significa che sta ottenendo meno della metà dei suoi competitor diretti (sia grandi che piccoli).

### 🌍 Indicatori del Mercato (Potenziale)
Questi valori descrivono l'ambiente esterno e la taglia degli incentivi disponibili.
* **Numero Aiuti per Azienda (Frequenza Operativa):** Indica quanti progetti di finanza agevolata le aziende hanno ricevuto mediamente nel periodo considerato. Una mediana alta indica un settore dinamico con molti bandi erogati, ma non necessariamente di grande impatto economico (che è, invece, definito dal **Budget per Azienda**)
* **Budget per Azienda (Intensità Economica):** Rappresenta il valore monetario dei contributi ottenuti mediamente da ogni azienda. Confrontare la **Mediana Target** con la **Mediana Totale** chiarisce se i fondi nel settore d'interesse (target) sono mediamente più ricchi o più poveri rispetto a un bando generico.
    * *Esempio:* Se il rapporto tra Mediana Target e Mediana Totale è il **25%**, significa che il finanziamento tipico nel settore target è grande un quarto rispetto a un finanziamento generico. Questo chiarisce se il settore target è composto da piccoli contributi o da grandi investimenti. 

### 🏢 Indicatori dell'Azienda (Specializzazione)
Fattori di FOCALIZZAZIONE (F). Questi valori dipendono dalle scelte strategiche della singola impresa.
* **Fattore Fo (Specializzazione Operativa):** Misura la focalizzazione del "fare". È la percentuale di pratiche nel settore target rispetto al totale delle pratiche gestite per un'azienda media. Se è vicina al 100%, l'azienda opera quasi esclusivamente nel target.
* **Fattore Fe (Specializzazione Economica):** Misura la focalizzazione del "valore". È la percentuale di budget target rispetto al budget totale incassato. Un valore alto indica che il core-business finanziario dell'azienda è strettamente legato al settore target.
    * *Esempio:* Se la **Mediana di F2 è il 15%**, significa che metà delle aziende analizzate dedica al settore target meno del 15% del proprio budget totale di aiuti, mentre l'altra metà di più. 
    * **Nota bene:** Questo valore indica il comportamento "tipo" delle aziende, ma non ci dice nulla su quanti soldi totali (massa monetaria) ci sono nel sistema.

---
💡 **Strategia:** Le aziende sotto mediana rappresentano il segmento con il più alto potenziale di crescita per nuove pianificazioni finanziarie o investimenti mirati.
"""


GUIDA_RICERCA = """
    **Dove cerchiamo le parole chiave?**
    
    Il sistema analizza ogni riga del database RNA verificando la presenza delle tue keywords in queste colonne ufficiali:
    1. `RNA_TITOLO_MISURA`
    2. `RNA_DESCRIZIONE_PROGETTO`
    3. `RNA_TITOLO_PROGETTO`
    
    *La ricerca non è case-sensitive (non distingue tra maiuscole e minuscole).*

    L'elenco completo dei parametri nel database RNA (nel caso vogliate implementare la ricerca delle parole target anche su altri campi):

    1. 'CAR'
    2. 'TITOLO_MISURA'
    3. 'DES_TIPO_MISURA'
    4. 'COD_CE_MISURA'
    5. 'BASE_GIURIDICA_NAZIONALE'
    6. 'LINK_TESTO_INTEGRALE_MISURA'
    7. 'IDENTIFICATIVO_UFFICIO'
    8. 'SOGGETTO_CONCEDENTE'
    9. 'COR'
    10. 'TITOLO_PROGETTO'
    11. 'DESCRIZIONE_PROGETTO'
    12. 'LINK_TRASPARENZA_NAZIONALE'
    13. 'DATA_CONCESSIONE'
    14. 'CUP'
    15. 'ATTO_CONCESSIONE'
    16. 'DENOMINAZIONE_BENEFICIARIO'
    17. 'CODICE_FISCALE_BENEFICIARIO'
    18. 'DES_TIPO_BENEFICIARIO'
    19. 'REGIONE_BENEFICIARIO'
    20. 'ID_COMPONENTE_AIUTO'
    21. 'COD_PROCEDIMENTO'
    22. 'DES_PROCEDIMENTO'
    23. 'COD_REGOLAMENTO'
    24. 'DES_REGOLAMENTO'
    25. 'COD_OBIETTIVO'
    26. 'DES_OBIETTIVO'
    27. 'SETTORE_ATTIVITA'
    28. 'ELEMENTO_DI_AIUTO'
    29. 'IMPORTO_NOMINALE'
    30. 'DES_STRUMENTO'
    31. 'COD_STRUMENTO'
    """
