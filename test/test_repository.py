
# Importiamo la funzione che vogliamo testare e la classe Documento 
# per verificare che il risultato sia effettivamente un oggetto Documento

import pytest
from sqlmodel import SQLModel, create_engine

import app.repository as repository
from app.models import DocumentoDB, ChunkDB


@pytest.fixture
def database_di_test(tmp_path, monkeypatch):

    # Creo un database SQLite temporaneo
    percorso = tmp_path / "test.db"
    engine_test = create_engine(f"sqlite:///{percorso}")

    # Creo le tabelle nel database temporaneo
    SQLModel.metadata.create_all(engine_test)

    # Faccio utilizzare al repository il database di test
    monkeypatch.setattr(repository, "engine", engine_test)


def test_salvataggio_e_recupero_chunks(database_di_test):

    # Creo un documento di prova
    documento = DocumentoDB(
        titolo="Documento di test",
        testo="Testo di prova",
        categoria="Legale",
        numero_pagine=2
    )

    # Salvo il documento nel database temporaneo
    documento_id = repository.aggiungi_documento_db(documento)

    # Creo due chunk associati al documento
    chunk_1 = ChunkDB(
        documento_id=documento_id,
        indice_chunk=0,
        numero_pagina=1,
        testo="Primo chunk",
        embedding=[0.1, 0.2, 0.3]
    )

    chunk_2 = ChunkDB(
        documento_id=documento_id,
        indice_chunk=1,
        numero_pagina=2,
        testo="Secondo chunk",
        embedding=[0.4, 0.5, 0.6]
    )

    # Salvo i chunk in ordine inverso
    repository.salva_chunks_db([chunk_2, chunk_1])

    # Recupero i chunk dal database
    recuperati = repository.recupera_chunks_db(documento_id)

    # Verifico il numero e l'ordine dei chunk
    assert len(recuperati) == 2
    assert recuperati[0].indice_chunk == 0
    assert recuperati[1].indice_chunk == 1

    # Verifico i dati salvati
    assert recuperati[0].testo == "Primo chunk"
    assert recuperati[1].numero_pagina == 2
    assert recuperati[0].embedding == [0.1, 0.2, 0.3]




def test_salvataggio_atomico_rollback(monkeypatch, tmp_path):
    import pytest
    from sqlalchemy.exc import StatementError
    from sqlmodel import SQLModel, Session, create_engine, select

    import app.repository as repository
    from app.models import DocumentoDB, ChunkDB

    # 1. Creo un database temporaneo isolato
    percorso_db = tmp_path / "test_atomic.db"
    engine_test = create_engine(f"sqlite:///{percorso_db}")

    # 2. Creo le tabelle
    SQLModel.metadata.create_all(engine_test)

    # 3. Faccio utilizzare al repository il database temporaneo
    monkeypatch.setattr(repository, "engine", engine_test)

    # 4. Creo un documento di prova
    documento = DocumentoDB(
        titolo="Test rollback",
        testo="Documento per testare il rollback",
        categoria="Test",
        numero_pagine=1
    )

    # 5. Preparo un chunk valido e uno con embedding non serializzabile
    dati_chunks = [
        {
            "indice_chunk": 0,
            "numero_pagina": 1,
            "testo": "Primo chunk",
            "embedding": [0.1, 0.2, 0.3]
        },
        {
            "indice_chunk": 1,
            "numero_pagina": 1,
            "testo": "Secondo chunk",
            "embedding": object()
        }
    ]

    # 6. Mi aspetto un errore durante il salvataggio dei chunk
    with pytest.raises(StatementError):
        repository.salva_documento_con_chunks_db(
            documento=documento,
            dati_chunks=dati_chunks
        )

    # 7. Controllo che il database sia rimasto vuoto
    with Session(engine_test) as session:

        documenti = session.exec(select(DocumentoDB)).all()
        chunks = session.exec(select(ChunkDB)).all()

        assert len(documenti) == 0
        assert len(chunks) == 0


    
