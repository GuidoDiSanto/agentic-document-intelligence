from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


# Definiamo una classe Python che rappresenta una tabella del database
class DocumentoDB(SQLModel, table=True):
    # Identificativo del documento. None indica che per un nuovo oggetto l'ID può non essere ancora assegnato.
    id: int | None = Field(default=None, primary_key=True)
    
    # Colonne della tabella
    titolo: str
    testo: str
    categoria: str
    numero_pagine: int
    elaborato: bool = False

class ChunkDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    documento_id: int = Field(foreign_key="documentodb.id", index=True)
    indice_chunk: int
    numero_pagina: int
    testo: str
    embedding: list[float] = Field(sa_column=Column(JSON))