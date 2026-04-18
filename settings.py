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

### 📊 Cos'è la Mediana?
A differenza della media (che può essere influenzata da pochi valori estremi - **outlier** - come un'azienda che riceve milioni di euro), la **Mediana** è il valore che divide esattamente in due la popolazione: il 50% delle aziende si trova sopra questo valore e il 50% sotto. 
Rappresenta quindi l'**azienda tipica** del settore: se un'azienda è sotto la mediana, significa che sta ottenendo meno della metà dei suoi competitor diretti (sia grandi che piccoli).

### 🌍 Indicatori del Mercato (Potenziale)
Questi valori descrivono l'ambiente esterno e la taglia degli incentivi disponibili.
* **Numero Aiuti per Azienda (Frequenza Operativa):** Indica quanti progetti di finanza agevolata le aziende hanno ricevuto mediamente nel periodo considerato. Una mediana alta indica un settore dinamico con molti bandi erogati.
* **Budget per Azienda (Intensità Economica):** Rappresenta il valore monetario dei contributi ottenuti mediamente da ogni azienda. Confrontare la Mediana Target con la Mediana Totale chiarisce se i fondi nel settore d'interesse (target) sono mediamente più ricchi o più poveri rispetto al mercato generale.
    * *Esempio:* Se il rapporto tra Mediana Target e Mediana Totale è il **25%**, significa che il finanziamento tipico nel settore target è grande un quarto rispetto a un finanziamento generico. Questo ci dice se il settore target è composto da piccoli contributi o da grandi investimenti.

### 🏢 Indicatori dell'Azienda (Specializzazione)
Fattori di FOCALIZZAZIONE (F). Questi valori dipendono dalle scelte strategiche della singola impresa.
* **Fattore Fo (Specializzazione Operativa):** Misura la focalizzazione del "fare". È la percentuale di pratiche nel settore target rispetto al totale delle pratiche gestite per un'azienda media. Se è vicina al 100%, l'azienda opera quasi esclusivamente nel target.
* **Fattore Fe (Specializzazione Economica):** Misura la focalizzazione del "valore". È la percentuale di budget target rispetto al budget totale incassato. Un valore alto indica che il core-business finanziario dell'azienda è strettamente legato al settore target.
    * *Esempio:* Se la **Mediana di F2 è il 15%**, significa che metà delle aziende analizzate dedica al settore target meno del 15% del proprio budget totale di aiuti, mentre l'altra metà di più. 
    * **Nota bene:** Questo valore indica il comportamento "tipo" delle aziende, ma non ci dice nulla su quanti soldi totali (massa monetaria) ci sono nel sistema.

---
💡 **Strategia:** Le aziende sotto mediana rappresentano il segmento con il più alto potenziale di crescita per nuove pianificazioni finanziarie o investimenti mirati.
"""

