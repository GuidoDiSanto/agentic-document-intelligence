# Agentic Document Intelligence

A modular document intelligence backend built with Python, FastAPI, SQLModel, and Sentence Transformers.

## Features

- PDF upload and text extraction using PyMuPDF
- Document chunking with overlap
- Multilingual sentence embeddings
- Dense retrieval with cosine similarity
- Cross-Encoder reranking
- Maximal Marginal Relevance (MMR) for result diversification
- SQLite persistence for documents, chunks, and embeddings
- REST API with FastAPI and interactive Swagger documentation
- Model-independent generation interface
- Mock LLM backend for testing the generation pipeline
- Automated tests with pytest

## Architecture

**Document indexing**

PDF Upload → Text Extraction → Chunking → Embeddings → SQLite

**Question answering pipeline**

User Query → Dense Retrieval → Cross-Encoder Reranking → MMR → Generation Interface → Response

## Installation

Requires Python 3.11.

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/agentic-document-intelligence.git
cd agentic-document-intelligence
```

Create and activate a virtual environment:

```bash
python3.11 -m venv agentic_intelligence
source agentic_intelligence/bin/activate
```

Install dependencies:

```bash
python -m pip install -e .
```

Start the API:

```bash
python -m uvicorn app.api:app --reload
```

API documentation is available at:

`http://127.0.0.1:8000/docs`

The SQLite database tables are initialized automatically at application startup.

## Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/pdf/upload` | Upload and index a PDF |
| POST | `/documenti/{documento_id}/domande` | Retrieve relevant document chunks |
| POST | `/documenti/{documento_id}/risposte` | Run retrieval and mock generation |
| GET | `/documenti-db/{documento_id}` | Retrieve document information |

## Testing

Run the automated tests:

```bash
python -m pytest -q
```

## Current Limitations

Real LLM-based answer generation is not included in the initial MVP.

A mock generator is used to avoid the additional memory and computational requirements of running a generative language model locally, as well as the costs of external LLM API calls.

The retrieval pipeline uses real embedding and reranking models, while the generation stage is simulated.

The embedding and reranking models are downloaded on first use and run locally.

The current retrieval implementation uses exact similarity computation rather than an approximate nearest-neighbor index.

## Future Improvements

Planned improvements are documented in [implementazioni_future.md](implementazioni_future.md).

## Project Status

**Version 0.1.0 — RAG Retrieval MVP with Mock Generation**

The project is intended as a portfolio and educational backend demonstrating modular RAG architecture, semantic retrieval, reranking, persistence, API development, and automated testing.