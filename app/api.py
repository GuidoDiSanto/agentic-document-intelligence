
# Importiamo la classe FastAPI dalla libreria fastapi
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi import UploadFile, File, Form
from fastapi import Depends
from pathlib import Path
import shutil
from app.models import DocumentoDB, ChunkDB
from app.repository import salva_chunks_db, recupera_chunks_db, recupera_documento_db, aggiungi_documento_db, modifica_titolo_documento_db, elimina_documento_db, recupera_documenti_db, recupera_documenti_cursor_db, salva_documento_con_chunks_db
import app.pdf_extractor as pdf_extractor
import app.chunking as chunking
from pydantic import BaseModel, Field , ConfigDict #Field permette di definire vincoli aggiuntivi 
from uuid import uuid4
from app.embedding_service import recupera_modello_embedding, recupera_modello_reranker
import numpy as np
import app.semantic_search as semantic_search
from app.generation_service import (GeneratoreLLM,recupera_generatore,genera_risposta)
from contextlib import asynccontextmanager
from app.database import inizializza_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inizializzo il database quando parte FastAPI
    inizializza_database()

    # L'applicazione rimane attiva
    yield

# Creiamo un oggetto della classe FastAPI
app = FastAPI(lifespan=lifespan)

# Definiamo la struttura dei dati che vogliamo ricevere
class DocumentoInput(BaseModel):
    titolo: str
    testo: str
    categoria: str
    numero_pagine: int = Field(gt=0, strict=True) #mettiamo condizione che il numero_pagine sia > 0

class DocumentoOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titolo: str
    categoria: str
    numero_pagine: int
    elaborato: bool

class PaginaDocumentiOutput(BaseModel):
    items: list[DocumentoOutput]
    next_cursor: int | None
    has_more: bool

class TitoloUpdate(BaseModel):
    titolo: str = Field(min_length=1)


class DomandaInput(BaseModel):
    domanda: str = Field(min_length=1)


class ChunkRisultatoOutput(BaseModel):
    indice: int
    numero_pagina: int
    testo: str
    dense_score: float
    rerank_score: float


class RisultatoRicercaOutput(BaseModel):
    documento_id: int
    domanda: str
    risultati: list[ChunkRisultatoOutput]

class RispostaRAGOutput(BaseModel):
    documento_id: int
    domanda: str
    risposta: str
    fonti: list[ChunkRisultatoOutput]

# Associamo la funzione seguente alle richieste HTTP GET dirette al percorso "/"
@app.get("/")
def home():
    # Restituiamo un dizionario Python
    return {"messaggio": "Agentic Document Intelligence attivo"}

@app.get("/stato")
def stato_sistema():
    return {"stato": "online", "progetto": "Agentic Document Intelligence", "versione": "0.1.0"}


@app.get("/documenti-db/{documento_id}", response_model=DocumentoOutput)
def informazioni_documento_db(documento_id: int):
    # 1. Recupera il documento dal repository
    documento = recupera_documento_db(documento_id)
    # 2. Se il documento è None, genera HTTPException 404
    # Se la funzione non ha trovato il documento, restituisce None
    if documento is None:
        # Traduciamo l'assenza del documento in un errore HTTP 404
        raise HTTPException(
            status_code=404,
            detail="Documento non trovato"
        )
    # 3. Se esiste, restituisci direttamente l'oggetto DocumentoDB
    return documento



# funzione post ma sul db
@app.post("/documenti-db", status_code=201)
def crea_documento_db(dati: DocumentoInput):
    nuovo_documento = DocumentoDB(
    titolo=dati.titolo,
    testo=dati.testo,
    categoria=dati.categoria,
    numero_pagine=dati.numero_pagine
    )

    nuovo_doc_id = aggiungi_documento_db(nuovo_documento)

    return{
        "id": nuovo_doc_id,
        "titolo": nuovo_documento.titolo,
        "testo" : nuovo_documento.testo,
        "numero_pagine": nuovo_documento.numero_pagine,
        "categoria": nuovo_documento.categoria
    }

@app.patch("/documenti-db/{documento_id}")
def aggiorna_titolo_documento_db(documento_id: int, dati: TitoloUpdate):
    # 1. Richiama modifica_titolo_documento_db() passando documento_id e il nuovo titolo
    documento = modifica_titolo_documento_db(documento_id, dati.titolo)
    # 2. Se la funzione restituisce None, genera HTTPException 404
    if documento is None: 
        raise HTTPException(
            status_code = 404,
            detail="Documento non trovato"
        )
    # 3. Altrimenti restituisci un dizionario contenente: id, titolo, categoria, numero_pagine
    return{
        "id": documento.id,
        "titolo": documento.titolo,
        "testo" : documento.testo,
        "numero_pagine": documento.numero_pagine,
        "categoria": documento.categoria
    }

@app.delete("/documenti-db/{documento_id}")
def elimina_documento_api_db(documento_id: int):
    result = elimina_documento_db(documento_id)
    # Se il documento non esiste, restituiamo HTTP 404
    if result is False:
        raise HTTPException(
            status_code=404,
            detail="Documento non trovato"
        )
    # Se è stato eliminato, restituiamo la conferma
    return {"eliminato": True}



@app.get("/documenti-db", response_model=list[DocumentoOutput])
def lista_documenti_db(categoria: str | None = None, limit: int | None = Query(default=None, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    documenti = recupera_documenti_db(
        categoria=categoria,
        limit=limit,
        offset=offset
    )
    # Creiamo una lista vuota per la risposta JSON
    lista = []
    # Convertiamo ogni DocumentoDB in un dizionario
    for documento in documenti:
        dizionario = {
            "id": documento.id,
            "titolo": documento.titolo,
            "testo": documento.testo,
            "categoria": documento.categoria,
            "numero_pagine": documento.numero_pagine,
            "elaborato": documento.elaborato
        }

        lista.append(dizionario)

    # FastAPI convertirà la lista in JSON
    return lista




@app.get( "/documenti-db/pagine/cursor", response_model=PaginaDocumentiOutput)
def lista_documenti_cursor_db( categoria: str | None = None, limit: int = Query(default=10, ge=1, le=100), after_id: int | None = Query(default=None, ge=0)):
    # 1. Recupera limit + 1 documenti dal repository
    documenti = recupera_documenti_cursor_db( categoria=categoria, limit=limit + 1, after_id=after_id)
    # 2. Calcola has_more confrontando il numero di risultati con limit, è una bool = True se la condizione è verificata sennò è false
    has_more = len(documenti) > limit
    # 3. Seleziona soltanto i primi limit documenti attraverso lo slicing
    items = documenti[:limit]
    # 4. Calcola next_cursor utilizzando l'ID dell'ultimo documento restituito
    if has_more and items:
        next_cursor = items[-1].id
    else:
        next_cursor = None

    # 5. Restituisci un dizionario con: "items", "next_cursor", "has_more"
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more
    }




@app.post("/pdf/upload", status_code=201)
def carica_pdf(file: UploadFile = File(...), categoria: str = Form(...)):
    '''
    Al termine della funzione abbiamo il pdf in data/uploads mentre le variabili:
        "id": nuovo_id,
        "titolo": nuovo_documento.titolo,
        "categoria": nuovo_documento.categoria,
        "numero_pagine": nuovo_documento.numero_pagine,
        "numero_chunks": len(chunks)

        le abbiamo dentro il db
    '''

    # 1. Verifica che il nome del file termini con .pdf Se non è così, genera HTTPException 400
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Il file deve essere un PDF")

    # 2. Crea la cartella data/uploads usando Path
    cartella = Path("data/uploads")
    cartella.mkdir(parents=True, exist_ok=True)

    # 3. Genera un percorso univoco con uuid4()
    percorso = cartella / f"{uuid4().hex}.pdf"

    # 4. Salva il file usando shutil.copyfileobj()
    with open(percorso, "wb") as destinazione:
        shutil.copyfileobj(file.file, destinazione)

    # 5. Estrai le pagine con estrai_pagine_pdf()
    pagine = pdf_extractor.estrai_pagine_pdf(str(percorso))

    # 6. Crea i chunk con crea_chunks()
    chunks = chunking.crea_chunks(pagine)

    if len(chunks) == 0:
        raise HTTPException(
            status_code=422,
            detail="Il PDF non contiene testo estraibile"
        )

    testi_chunks = []

    for chunk in chunks:
        testi_chunks.append(chunk["testo"])

    modello = recupera_modello_embedding()

    embeddings = modello.encode(
        testi_chunks,
        batch_size=4
    )

    # 7. Unisci il testo delle pagine con join()
    testi = []
    for pagina in pagine:
        testi.append(pagina["testo"])

    testo_completo = "\n\n".join(testi)

    # 8. Crea un oggetto DocumentoDB
    nuovo_documento = DocumentoDB(
        titolo=Path(file.filename).stem,
        testo=testo_completo,
        categoria=categoria,
        numero_pagine=len(pagine)
    )

    # 9. Preparo i dati dei chunk da salvare insieme al documento
    dati_chunks = []

    for indice, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        dati_chunks.append({
            "indice_chunk": indice,
            "numero_pagina": chunk["numero_pagina"],
            "testo": chunk["testo"],
            "embedding": embedding.tolist()
        })

    # 10. Salvo documento e chunk in una singola transazione SQLite
    try:
        nuovo_id = salva_documento_con_chunks_db(
        documento=nuovo_documento,
        dati_chunks=dati_chunks
    )
    except Exception:
        # Se il salvataggio fallisce, elimino anche il PDF appena caricato
        percorso.unlink(missing_ok=True)
        raise
    
    # 11. Restituisco id, titolo, categoria, numero_pagine e numero_chunks
    return {
        "id": nuovo_id,
        "titolo": nuovo_documento.titolo,
        "categoria": nuovo_documento.categoria,
        "numero_pagine": nuovo_documento.numero_pagine,
        "numero_chunks": len(chunks)
    }



@app.post("/documenti/{documento_id}/domande", response_model=RisultatoRicercaOutput)
def interroga_documento(documento_id: int, dati: DomandaInput):

    # 1. Verifico che la domanda non sia vuota
    # strip() rimuove spazi a inizio e fine della stringa
    domanda = dati.domanda.strip()
    if not domanda:
        raise HTTPException(
            status_code=422,
            detail="La domanda non può essere vuota"
        )

    # 2. Verifico che il documento esista
    documento = recupera_documento_db(documento_id)
    if documento is None:
        raise HTTPException(
            status_code=404,
            detail="Documento non trovato"
        )

    # 3. Recupero i chunk salvati nel database
    chunks_db = recupera_chunks_db(documento_id)
    if len(chunks_db) == 0:
        raise HTTPException(
            status_code=409,
            detail="Il documento non contiene chunk indicizzati"
        )

    # 4. Ricostruisco la lista dei chunk
    chunks = []
    for chunk_db in chunks_db:
        chunk = {
            "numero_pagina": chunk_db.numero_pagina,
            "testo": chunk_db.testo
        }
        chunks.append(chunk)

    # 5. Ricostruisco la matrice degli embeddings
    lista_embeddings = []
    for chunk_db in chunks_db:
        lista_embeddings.append(chunk_db.embedding)

    embeddings = np.array(lista_embeddings, dtype=np.float32)   

    # 6. Recupero i modelli già caricati, oppure li carico la prima volta
    modello = recupera_modello_embedding()
    reranker = recupera_modello_reranker()

    # 7. Eseguo la pipeline completa di retrieval
    risultati = semantic_search.retrieval_completo(
        domanda=domanda,
        chunks=chunks,
        embeddings=embeddings,
        modello=modello,
        reranker=reranker,
        top_n=8,
        soglia=0.3,
        k=3,
        lambda_mmr=0.7
    )

    # 8. Restituisco i risultati
    return {
        "documento_id": documento_id,
        "domanda": domanda,
        "risultati": risultati
    }



@app.post("/documenti/{documento_id}/risposte", response_model=RispostaRAGOutput)
def genera_risposta_documento(documento_id: int, dati: DomandaInput, generatore: GeneratoreLLM = Depends(recupera_generatore)):

    # 1. Recupero i risultati della pipeline di retrieval
    ricerca = interroga_documento(documento_id, dati)

    # 2. Estraggo i chunk selezionati da MMR
    risultati = ricerca["risultati"]

    # 3. Genero la risposta utilizzando il generatore configurato
    risposta = genera_risposta(
        domanda=ricerca["domanda"],
        risultati=risultati,
        generatore=generatore
    )

    # 4. Restituisco la risposta e i chunk utilizzati
    return {
        "documento_id": documento_id,
        "domanda": ricerca["domanda"],
        "risposta": risposta,
        "fonti": risultati
    }
