
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from app.api import app
import app.repository as repository

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
