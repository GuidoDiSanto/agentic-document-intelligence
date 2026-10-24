# Importiamo Path per gestire il percorso del database
from pathlib import Path
from sqlmodel import SQLModel, create_engine
import app.models


# Definiamo il percorso del database.  Utilizziamo un nuovo file per non interferire con l'eventuale database creato con sqlite3.
PERCORSO_DB = (
    Path(__file__).resolve().parent.parent
    / "documenti_sqlmodel.db"
)

# Creiamo l'engine che configura la comunicazione con il database SQLite. echo=True mostra le istruzioni SQL eseguite.
engine = create_engine(
    f"sqlite:///{PERCORSO_DB}",
    echo=False
)

# Funzione che crea le tabelle mancanti
def inizializza_database():
    # SQLModel legge i modelli registrati e crea le relative tabelle se non esistono.
    SQLModel.metadata.create_all(engine)


# Eseguiamo queste istruzioni soltanto quando avviamo direttamente questo modulo.
if __name__ == "__main__":
    # Inizializziamo il database
    inizializza_database()
    # Stampiamo un messaggio di conferma
    print(f"Database SQLModel inizializzato: {PERCORSO_DB}")



def inizializza_database():
    # Importo i modelli per registrare entrambe le tabelle
    import app.models

    # Creo le tabelle solo se non esistono già
    SQLModel.metadata.create_all(engine)