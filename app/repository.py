from sqlmodel import Session, select # Session permette di lavorare con i dati del database.
from app.database import engine #  L'engine contiene le informazioni necessarie per comunicare con il nostro database SQLite.
from app.models import DocumentoDB, ChunkDB


#funzione per recuperare un documento tramite id ma dal db 
def recupera_documento_db(documento_id: int)-> DocumentoDB | None:
    with Session(engine) as session:
        query = select(DocumentoDB).where(DocumentoDB.id == documento_id)
        risultato = session.exec(query)
        documento = risultato.first()
        return(documento)
    

def recupera_documenti_db( categoria: str | None = None, limit: int | None = None, offset: int = 0) -> list[DocumentoDB]:
    with Session(engine) as session:
        # Costruiamo la query iniziale
        query = select(DocumentoDB)

        if categoria is not None:
            query = query.where(
                DocumentoDB.categoria == categoria
            )

        query = query.order_by(DocumentoDB.id)

        if limit is not None:
            query = query.limit(limit)

        query = query.offset(offset)
        risultato = session.exec(query)
        return risultato.all()



def recupera_documenti_cursor_db(categoria: str | None = None, limit: int = 10, after_id: int | None = None) -> list[DocumentoDB]:
    with Session(engine) as session:
        query = select(DocumentoDB)
        # Applichiamo il filtro per categoria, se presente
        if categoria is not None:
            query = query.where(
                DocumentoDB.categoria == categoria
            )
        if after_id is not None:
            query = query.where(
                DocumentoDB.id > after_id
            )
        query = query.order_by(DocumentoDB.id)
        query = query.limit(limit)
        risultato = session.exec(query)

        return risultato.all()
     


#funzione per aggiungere un documento ma al db
def aggiungi_documento_db(nuovo_documento: DocumentoDB) -> int:
    with Session(engine) as session: 
        session.add(nuovo_documento)
        session.commit()
        session.refresh(nuovo_documento)
        return nuovo_documento.id
    

def modifica_titolo_documento_db(documento_id: int, nuovo_titolo: str) -> DocumentoDB | None:
    '''
    La funzione deve:
    1. Aprire una sessione con Session(engine).
    2. Cercare il documento utilizzando session.get().
    3. Se il documento non esiste, restituire None.
    4. Se esiste, modificare il suo attributo titolo assegnandogli nuovo_titolo.
    5. Confermare la modifica attraverso commit().
    6. Ricaricare l'oggetto attraverso refresh().
    7. Restituire il documento aggiornato.'''
    with Session(engine) as session: 
        documento = session.get(DocumentoDB, documento_id)
        if documento is None : return None 
        documento.titolo = nuovo_titolo
        session.commit()
        session.refresh(documento)
        return documento
    

def elimina_documento_db(documento_id: int) -> bool:
    with Session(engine) as session: 
        documento = session.get(DocumentoDB, documento_id)
        if documento is None : return False
        session.delete(documento)
        session.commit()
        return True 


def salva_chunks_db(chunks: list[ChunkDB]) -> None:
    with Session(engine) as session:
        session.add_all(chunks)
        session.commit()


def recupera_chunks_db(documento_id: int) -> list[ChunkDB]:
    with Session(engine) as session:

        query = (
            select(ChunkDB).where(ChunkDB.documento_id == documento_id).order_by(ChunkDB.indice_chunk)
        )

        chunks = session.exec(query).all()

        return list(chunks)



def salva_documento_con_chunks_db(
    documento: DocumentoDB,
    dati_chunks: list[dict]
) -> int:

    # 1. Apro una sessione con il database SQLite
    with Session(engine, expire_on_commit=False) as session:

        # 2. Inizio una transazione atomica
        # Se tutte le operazioni riescono, viene eseguito il COMMIT  Se si verifica un errore, viene eseguito il ROLLBACK
        with session.begin():

            # 3. Aggiungo il documento alla sessione
            session.add(documento)

            # 4. Eseguo l'INSERT senza confermare la transazione In questo modo il database assegna l'ID al documento
            session.flush()

            # 5. Recupero l'ID generato dal database
            nuovo_id = documento.id

            if nuovo_id is None:
                raise RuntimeError("Impossibile ottenere l'ID del documento")

            # 6. Creo i record ChunkDB associati al documento
            chunks_db = []

            for dati in dati_chunks:
                chunk_db = ChunkDB(
                    documento_id=nuovo_id,
                    indice_chunk=dati["indice_chunk"],
                    numero_pagina=dati["numero_pagina"],
                    testo=dati["testo"],
                    embedding=dati["embedding"]
                )

                chunks_db.append(chunk_db)

            # 7. Aggiungo tutti i chunk alla stessa transazione
            session.add_all(chunks_db)

        # 8. Arrivati qui, la transazione è stata confermata
        return nuovo_id
