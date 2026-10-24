
# Importiamo TestClient, lo strumento che permette di simulare richieste HTTP alla nostra applicazione
from fastapi.testclient import TestClient
import app.repository as repository
from sqlmodel import SQLModel, create_engine
import app.api as api
from app.api import app
import pytest
from pathlib import Path


# Creiamo un client di test associato all'applicazione
client = TestClient(app)


def test_get_documento_db_inesistente():
        #1. Simulare una richiesta GET /documenti-db/999.
        risposta = client.get("/documenti-db/999")
        #2. Verificare che lo status code sia 404.
        assert risposta.status_code == 404
         # 3. Verificare che il JSON contenga "detail": "Documento non trovato"
        # Convertiamo il JSON in un dizionario Python
        dati = risposta.json()
        assert dati["detail"] == "Documento non trovato"


def test_upload_pdf(monkeypatch, tmp_path):
    percorso_pdf = Path("data/esempio.pdf").resolve()

    percorso_db_test = tmp_path / "test_upload.db"
    engine_test = create_engine(f"sqlite:///{percorso_db_test}")
    SQLModel.metadata.create_all(engine_test)

    monkeypatch.setattr(repository, "engine", engine_test)
    monkeypatch.chdir(tmp_path)

    client = TestClient(app)

    with open(percorso_pdf, "rb") as pdf:
        response = client.post(
            "/pdf/upload",
            files={"file": ("esempio.pdf", pdf, "application/pdf")},
            data={"categoria": "Legale"}
        )

    assert response.status_code == 201

    dati = response.json()

    assert dati["titolo"] == "esempio"
    assert dati["categoria"] == "Legale"
    assert dati["numero_pagine"] == 3
    assert dati["numero_chunks"] > 0

    cartella_uploads = tmp_path / "data" / "uploads"
    file_salvati = list(cartella_uploads.glob("*.pdf"))

    assert len(file_salvati) == 1

    risposta_get = client.get(f"/documenti-db/{dati['id']}")

    assert risposta_get.status_code == 200
    assert risposta_get.json()["titolo"] == "esempio"



def test_endpoint_risposte_mock(monkeypatch):
    from fastapi.testclient import TestClient
    import app.api as api

    def retrieval_finto(documento_id, dati):
        return {
            "documento_id": documento_id,
            "domanda": dati.domanda,
            "risultati": [
                {
                    "indice": 0,
                    "numero_pagina": 2,
                    "testo": "Il documento prevede tre fasi.",
                    "dense_score": 0.85,
                    "rerank_score": 2.1
                }
            ]
        }

    monkeypatch.setattr(
        api,
        "interroga_documento",
        retrieval_finto
    )

    with TestClient(api.app) as client:
        risposta = client.post(
            "/documenti/12/risposte",
            json={"domanda": "Quali sono le fasi?"}
        )

    assert risposta.status_code == 200

    dati = risposta.json()

    assert dati["documento_id"] == 12
    assert "MOCK" in dati["risposta"]
    assert "Contesto ricevuto:" in dati["risposta"]
    assert len(dati["fonti"]) == 1
    assert dati["fonti"][0]["numero_pagina"] == 2



def test_domanda_documento_inesistente(monkeypatch):

    # Simulo un repository che non trova il documento richiesto
    monkeypatch.setattr(
        api,
        "recupera_documento_db",
        lambda documento_id: None
    )

    # Interrogo un documento inesistente
    with TestClient(api.app) as client:
        risposta = client.post(
            "/documenti/999/domande",
            json={"domanda": "Quali sono le tre fasi?"}
        )

    # Verifico che l'API restituisca HTTP 404
    assert risposta.status_code == 404
    assert risposta.json()["detail"] == "Documento non trovato"


def test_domanda_documento_senza_chunks(monkeypatch):

    # Simulo un documento esistente
    monkeypatch.setattr(
        api,
        "recupera_documento_db",
        lambda documento_id: object()
    )

    # Simulo un documento senza chunk indicizzati
    monkeypatch.setattr(
        api,
        "recupera_chunks_db",
        lambda documento_id: []
    )

    # Interrogo il documento
    with TestClient(api.app) as client:
        risposta = client.post(
            "/documenti/1/domande",
            json={"domanda": "Quali sono le tre fasi?"}
        )

    # Verifico che l'API restituisca HTTP 409
    assert risposta.status_code == 409
    assert risposta.json()["detail"] == (
        "Il documento non contiene chunk indicizzati"
    )
