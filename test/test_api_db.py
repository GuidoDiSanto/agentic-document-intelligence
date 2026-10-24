
import pytest

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from app.models import DocumentoDB
import app.repository as repository
from app.api import app


# Questa fixture prepara un database temporaneo che verrà utilizzato durante il test.
@pytest.fixture
def database_test(monkeypatch, tmp_path):
    # 1. Definiamo il percorso del database temporaneo.
    percorso_db = tmp_path / "test_documenti.db"
    # 2. Creiamo un engine collegato al database temporaneo.
    engine_test = create_engine(
        f"sqlite:///{percorso_db}"
    )
    # 3. Creiamo le tabelle nel database temporaneo.
    SQLModel.metadata.create_all(engine_test)
    # 4. Sostituiamo temporaneamente l'engine del repository.
    monkeypatch.setattr(
        repository,
        "engine",
        engine_test
    )


# Testiamo che il database appena creato sia vuoto.
def test_database_inizialmente_vuoto(database_test):

    # Creiamo un client per simulare richieste HTTP.
    client = TestClient(app)

    # Cerchiamo un documento con ID 1.
    risposta = client.get("/documenti-db/1")

    # Il documento non deve esistere nel database di test.
    assert risposta.status_code == 404

    # Verifichiamo anche il messaggio restituito dall'API.
    assert risposta.json()["detail"] == "Documento non trovato"


def test_creazione_e_recupero_documento_db(database_test):
    # 1. Crea un TestClient
    client = TestClient(app)
    # 2. Invia una richiesta POST con un documento valido
    risposta = client.post(
    "/documenti-db",
    json={
        "titolo": "Documento test",
        "testo": "Questo è un documento di prova",
        "categoria": "Legale",
        "numero_pagine": 5
    }
    )
    # 3. Verifica che la risposta abbia status code 201
    assert risposta.status_code == 201
    # 4. Recupera l'ID dal JSON della risposta
    dati_risposta = risposta.json()
    id_nuovo_doc = dati_risposta["id"]
    # 5. Esegui una GET utilizzando quell'ID
    risposta_get = client.get(f"/documenti-db/{id_nuovo_doc}")
    dati_risposta_get = risposta_get.json()
    # 6. Verifica che la GET restituisca status code 200
    assert risposta_get.status_code == 200
    # 7. Verifica che il titolo recuperato sia uguale a "Documento test"
    assert dati_risposta_get["titolo"] == "Documento test"


def test_modifica_titolo_documento_db(database_test):

    # 1. Crea un oggetto DocumentoDB Titolo: "Contratto originale" Numero pagine: 10
    documento = DocumentoDB(
        titolo="Contratto originale",
        testo="Testo del contratto",
        categoria="Legale",
        numero_pagine=10
    )
    # 2. Salvalo utilizzando aggiungi_documento_db() e memorizza l'ID restituito
    id_nuovo_doc = repository.aggiungi_documento_db(documento)
    # 3. Chiama modifica_titolo_documento_db() passando l'ID e il titolo "Contratto aggiornato"
    nuovo_doc = repository.modifica_titolo_documento_db(id_nuovo_doc, "Contratto aggiornato")
    # 4. Recupera nuovamente il documento tramite recupera_documento_db()
    doc_recuperato = repository.recupera_documento_db(id_nuovo_doc)
    # 5. Verifica con assert che: il titolo sia "Contratto aggiornato"  l'ID sia lo stesso  il numero di pagine sia ancora 10
    assert doc_recuperato.titolo == "Contratto aggiornato"
    assert id_nuovo_doc == doc_recuperato.id
    assert doc_recuperato.numero_pagine == 10

def test_modifica_documento_inesistente(database_test):
    # Chiama modifica_titolo_documento_db() con ID 999
    doc_mod = repository.modifica_titolo_documento_db(999, "contratto inesistente")

    # Verifica che il risultato sia None
    assert doc_mod == None

def test_patch_titolo_documento_db(database_test):
    '''
    Creare un documento nel database temporaneo attraverso client.post().
    Recuperare l'ID dalla risposta.
    Eseguire client.patch() sull'ID ottenuto, inviando un nuovo titolo.
    Verificare che PATCH restituisca HTTP 200.
    Eseguire client.get() sullo stesso documento.
    Verificare che il titolo sia quello aggiornato.
    '''
    # Prepariamo il documento
    dati_documento = {
        "titolo": "Documento test",
        "testo": "Testo di prova",
        "categoria": "Legale",
        "numero_pagine": 5
    }
    client = TestClient(app)
    risposta = client.post(
        "/documenti-db",
        json = dati_documento
    )
    assert risposta.status_code == 201
    dati_risposta = risposta.json()
    documento_id = dati_risposta["id"]

    risposta1 = client.patch(
        f"/documenti-db/{documento_id}",
        json={"titolo": "Titolo aggiornato"}
    )
    assert risposta1.status_code == 200

    risposta2 = client.get(f"/documenti-db/{documento_id}")
    dati_risposta2 = risposta2.json()
    assert dati_risposta2["titolo"] == "Titolo aggiornato"

def test_delete_documento_db(database_test):
    # Prepariamo il documento
    dati_documento = {
        "titolo": "Documento test",
        "testo": "Testo di prova",
        "categoria": "Legale",
        "numero_pagine": 5
    }
    client = TestClient(app)
    risposta = client.post(
        "/documenti-db",
        json = dati_documento
    )
    assert risposta.status_code == 201
    dati_risposta = risposta.json()
    documento_id = dati_risposta["id"]

    risposta1 = client.delete(f"/documenti-db/{documento_id}")
    assert risposta1.status_code == 200
    assert risposta1.json()["eliminato"] is True

    # Proviamo a recuperare il documento eliminato
    risposta2 = client.get(f"/documenti-db/{documento_id}")
    # Il documento non deve più esistere
    assert risposta2.status_code == 404

def test_delete_documento_inesistente(database_test): 
    client = TestClient(app)
    risposta = client.delete(f"/documenti-db/{999}")
    assert risposta.status_code == 404

def test_patch_titolo_non_valido(database_test):
    '''
    Dovrai creare un documento tramite client.post(), recuperarne l'ID,
    tentare di modificarne il titolo inviando una stringa vuota con client.patch(), 
    verificare che la risposta sia 422 e infine fare una GET per controllare che il titolo originale non sia cambiato.
    '''
    client = TestClient(app)
    dati_documento = {
        "titolo": "Documento test",
        "testo": "Testo di prova",
        "categoria": "Legale",
        "numero_pagine": 5
    } 
    risposta = client.post(
        "/documenti-db",
        json = dati_documento
    )
    assert risposta.status_code == 201
    dati_risposta = risposta.json()
    documento_id = dati_risposta["id"]
    # 5. Proviamo a modificare il titolo con una stringa vuota
    risposta_patch = client.patch(
        f"/documenti-db/{documento_id}",
        json={"titolo": ""}
    )
    assert risposta_patch.status_code == 422

    risposta_get = client.get(
        f"/documenti-db/{documento_id}"
    )
    assert risposta_get.status_code == 200
    documento_recuperato = risposta_get.json()
    assert documento_recuperato["titolo"] == "Documento test"



def test_lista_documenti_db(database_test):
    # Creiamo il client HTTP di test
    client = TestClient(app)
    dati_documento1 = {
        "titolo": "Documento test 1",
        "testo": "Testo di prova 1",
        "categoria": "Legale 1",
        "numero_pagine": 5
    }
    dati_documento2 = {
        "titolo": "Documento test 2",
        "testo": "Testo di prova 2",
        "categoria": "Legale 2",
        "numero_pagine": 10
    }

    risposta1 = client.post(
        "/documenti-db",
        json=dati_documento1
    )
    risposta2 = client.post(
        "/documenti-db",
        json=dati_documento2
    )

    # Verifichiamo che entrambi siano stati creati
    assert risposta1.status_code == 201
    assert risposta2.status_code == 201

    # Recuperiamo TUTTI i documenti con una sola GET
    risposta_get = client.get("/documenti-db")
    # Verifichiamo che la richiesta sia riuscita
    assert risposta_get.status_code == 200

    # Convertiamo il JSON in una lista Python
    documenti = risposta_get.json()

    # Verifichiamo che ci siano esattamente due documenti
    assert len(documenti) == 2

    # Creiamo una lista che conterrà soltanto i titoli
    titoli = []
    # Scorriamo la lista dei documenti restituiti
    for documento in documenti:
        # Ogni documento è un dizionario Python
        titoli.append(documento["titolo"])

    # Verifichiamo la presenza dei due titoli
    assert "Documento test 1" in titoli
    assert "Documento test 2" in titoli


def test_paginazione_documenti_db(database_test):

    # Creiamo il client per simulare richieste HTTP
    client = TestClient(app)
   
    for i in range(1, 6):
        # Prepariamo i dati del documento corrente
        dati_documento = {
            "titolo": f"Documento test {i}",
            "testo": f"Testo di prova {i}",
            "categoria": f"Legale {i}",
            "numero_pagine": i * 5
        }

        # Inviamo una POST per salvare il documento
        risposta = client.post(
            "/documenti-db",
            json=dati_documento
        )

        # Verifichiamo che il documento sia stato creato
        assert risposta.status_code == 201

    # Recuperiamo 2 documenti, saltando i primi 2
    risposta_get = client.get(
        "/documenti-db",
        params={
            "limit": 2,
            "offset": 2
        }
    )

    # Verifichiamo che la GET sia riuscita
    assert risposta_get.status_code == 200

    # Convertiamo la risposta JSON in una lista Python
    documenti = risposta_get.json()

    # Verifichiamo il numero dei documenti restituiti
    assert len(documenti) == 2

    # Verifichiamo i titoli dei documenti
    assert documenti[0]["titolo"] == "Documento test 3"
    assert documenti[1]["titolo"] == "Documento test 4"

def test_paginazione_limit_non_valido(database_test):
    client = TestClient(app)
    risposta_get = client.get(
        "/documenti-db",
        params={
            "limit" : -5
        }
    )

    assert risposta_get.status_code == 422