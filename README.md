# Agentic Document Intelligence

**A modular Retrieval-Augmented Generation (RAG) backend for intelligent PDF document processing, semantic search, and context retrieval.**

Agentic Document Intelligence is a Python-based project designed to explore and implement the core components of a modern document intelligence system.

The main objective is to build a backend capable of **processing PDF documents, extracting and indexing their contents, and retrieving the most relevant information in response to natural-language questions**.

Unlike traditional keyword-based search, the system uses multilingual sentence embeddings to identify semantically relevant passages, even when the terminology used in a question differs from the wording found in the document.

The project focuses on the **retrieval component of RAG architectures**, combining dense vector search, Cross-Encoder reranking, and Maximal Marginal Relevance (MMR) to improve the relevance and diversity of retrieved information.

The architecture also includes a model-independent generation interface, designed to support future integration with different Large Language Models (LLMs).

**Current status:** The document indexing and retrieval pipelines use real Machine Learning models. The final answer-generation stage uses a mock LLM, allowing the complete application workflow to be tested without running an additional generative model or relying on paid API services.

---

## 1. Project Objectives

The project was developed to investigate how different components of a RAG system can be integrated into a modular and extensible backend.

Its main objectives are:

- Build an end-to-end document ingestion and semantic retrieval pipeline.
- Process PDF files while preserving document and page-level metadata.
- Generate and persist multilingual vector embeddings.
- Retrieve relevant document passages using semantic similarity.
- Improve retrieval quality through Cross-Encoder reranking.
- Reduce redundant information using Maximal Marginal Relevance.
- Expose the system through RESTful API endpoints.
- Separate document retrieval from answer generation.
- Design a generation interface compatible with future local or API-based LLM backends.
- Validate the implementation using automated tests.

The emphasis is on **backend architecture, information retrieval, and modular ML system design**, rather than on training language models from scratch.

---

## 2. System Architecture

The system is organized into two main pipelines: document indexing and question processing.

### 2.1 Document Indexing Pipeline

When a PDF is uploaded, the system performs the following operations:

**PDF Upload → Text Extraction → Chunking → Embedding Generation → SQLite Persistence**

**Step 1 — PDF Extraction**

The document is processed using PyMuPDF, which extracts text and preserves information about the page from which it originated.

**Step 2 — Text Chunking**

The extracted text is divided into smaller, partially overlapping chunks.

Overlapping chunks help preserve contextual continuity between adjacent text segments.

**Step 3 — Embedding Generation**

Each chunk is converted into a numerical vector using a pretrained multilingual Sentence Transformer.

The embedding model maps semantically similar text passages to nearby representations in vector space.

**Step 4 — Database Persistence**

Document metadata, extracted chunks, page references, and embedding vectors are stored in SQLite using SQLModel.

Documents and their associated chunks are saved within a single database transaction to prevent partially indexed records.

### 2.2 Semantic Retrieval Pipeline

When a user submits a question, the system executes a multi-stage retrieval pipeline:

**User Question → Query Embedding → Dense Retrieval → Cross-Encoder Reranking → MMR → Relevant Context**

**Step 1 — Query Embedding**

The user's question is converted into a vector using the same embedding model employed during document indexing.

**Step 2 — Dense Retrieval**

Cosine similarity is computed between the query vector and stored chunk embeddings.

The system retrieves the highest-scoring candidates, applying a configurable similarity threshold to discard insufficiently relevant passages.

**Step 3 — Cross-Encoder Reranking**

A separate Cross-Encoder model evaluates each question–chunk pair.

Unlike the initial dense retrieval stage, which compares independently generated embeddings, the Cross-Encoder processes the question and candidate passage jointly to estimate their relevance.

Candidates are reordered according to their reranking scores.

**Step 4 — Maximal Marginal Relevance (MMR)**

The final selection uses MMR to balance two objectives:

- **Relevance:** selecting passages that are strongly related to the user's question.
- **Diversity:** avoiding the selection of multiple passages containing largely redundant information.

The resulting chunks are returned with their document page references and retrieval scores.

### 2.3 Generation Interface

The selected passages can be passed to a separate generation component.

The current implementation defines a common generator interface using Python's `Protocol`, allowing different implementations to be integrated without changing the retrieval pipeline.

A mock generator is currently used to verify that the question and retrieved context are correctly transmitted through the application.

**The mock does not perform natural-language answer generation.** It returns a clearly identified diagnostic response while preserving the retrieved sources.

This architecture is intended to support real LLM integration in future versions.

---

## 3. Technologies

| Component | Technology |
|---|---|
| Programming language | Python 3.11 |
| REST API | FastAPI |
| Data validation | Pydantic |
| Database and ORM | SQLite, SQLModel |
| PDF extraction | PyMuPDF |
| Dense embeddings | Sentence Transformers |
| Reranking | Cross-Encoder |
| Numerical operations | NumPy |
| Retrieval diversification | Maximal Marginal Relevance |
| Generation interface | Python Protocol, Dependency Injection |
| Automated testing | pytest, FastAPI TestClient |

### Machine Learning Models

**Embedding model**

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Used to generate 384-dimensional multilingual sentence embeddings for document chunks and user queries.

**Reranking model**

`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`

Used to rerank candidate passages based on their relevance to the input question.

Both models are downloaded on first use and run locally on the CPU.

No paid API service is required for the current implementation.

---

## 4. Installation

### Requirements

- Python 3.11
- Internet connection for the initial download of pretrained models
- Sufficient local memory to load the embedding and reranking models

### Clone the Repository

```bash
git clone https://github.com/GuidoDiSanto/agentic-document-intelligence.git
cd agentic-document-intelligence
```

### Create a Virtual Environment

```bash
python3.11 -m venv agentic_intelligence
source agentic_intelligence/bin/activate
```

### Install Dependencies

```bash
python -m pip install -e .
```

### Start the API Server

```bash
python -m uvicorn app.api:app --reload
```

The interactive API documentation is available at:

**http://127.0.0.1:8000/docs**

SQLite database tables are initialized automatically when the application starts.

---

## 5. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/pdf/upload` | Upload a PDF, extract text, generate embeddings, and store indexed chunks |
| POST | `/documenti/{documento_id}/domande` | Execute semantic retrieval, reranking, and MMR |
| POST | `/documenti/{documento_id}/risposte` | Execute retrieval and the mock generation stage |
| GET | `/documenti-db/{documento_id}` | Retrieve document information |

### Example: Upload a PDF

```bash
curl -X POST "http://127.0.0.1:8000/pdf/upload" \
  -F "file=@data/esempio.pdf" \
  -F "categoria=Legale"
```

The API returns the document ID, title, category, number of pages, and number of indexed chunks.

### Example: Ask a Question

After uploading the document, use the ID returned by the upload endpoint:

```bash
curl -X POST "http://127.0.0.1:8000/documenti/1/domande" \
  -H "Content-Type: application/json" \
  -d '{"domanda": "Quali sono le tre fasi di elaborazione dei PDF?"}'
```

Replace `1` with the actual ID of the uploaded document.

The response contains the retrieved passages, their page numbers, dense similarity scores, and Cross-Encoder reranking scores.

To test the generation interface, send the same request to:

`POST /documenti/{documento_id}/risposte`

This endpoint returns the mock response and the retrieved passages used as context.

---

## 6. Testing

The project includes automated tests covering API behavior, database operations, document processing, and selected application workflows.

Tests use temporary SQLite databases and mocked dependencies where appropriate to avoid modifying application data or requiring unnecessary model inference.

Run the test suite using:

```bash
python -m pytest -q
```

---

## 7. Design Decisions and Current Limitations

### Mock LLM Instead of Real Generation

The initial version deliberately uses a mock generation backend.

Running a generative LLM locally would require additional computational resources and memory, while calling external LLM APIs could introduce usage-based costs.

For a personal project, the decision was to prioritize the development and validation of the retrieval architecture without incurring those additional costs.

The system is therefore **generation-ready from an architectural perspective**, but real AI-generated answers are not currently supported.

### Exact Vector Search

Embeddings are stored in SQLite, and similarity is computed using NumPy.

This provides a simple and transparent implementation suitable for small datasets and educational experimentation.

For larger document collections, an approximate nearest-neighbor index or dedicated vector database could improve retrieval efficiency.

### Chunking Strategy

The current implementation uses character-based chunking with overlap.

Future improvements may introduce sentence-aware or token-aware chunking to better preserve linguistic structure and contextual boundaries.

### Scope

Despite its name, the current version focuses on document intelligence and RAG infrastructure. It does not yet implement autonomous multi-agent workflows.

The modular backend is intended to provide a foundation for more advanced document-processing and agent-based applications.

---

## 8. Future Improvements

Potential extensions include:

- Integration with configurable local or remote LLM backends.
- More advanced document chunking strategies.
- Approximate nearest-neighbor search and vector indexing.
- Retrieval quality evaluation and benchmarking.
- Support for larger document collections.
- Further improvements to error handling and scalability.

Additional implementation details and architectural considerations are documented in [future_implementations.md](future_implementations.md).

---

## 9. Project Status

**Version 0.1.0 — RAG Retrieval MVP with Mock Generation**

The current version demonstrates a functioning semantic document retrieval backend with PDF ingestion, persistent vector representations, Cross-Encoder reranking, MMR-based context selection, REST API endpoints, and automated tests.

The project is developed as a **personal AI Engineering portfolio project**, with particular emphasis on practical RAG implementation, modular software architecture, backend development, and integration of pretrained Machine Learning models.
