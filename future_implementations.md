# Future Improvements — Agentic Document Intelligence

This document tracks potential architectural improvements, technical limitations, and future extensions of the Agentic Document Intelligence project.

The initial implementation prioritizes simplicity, maintainability, and the development of a fully functional RAG (Retrieval-Augmented Generation) pipeline.

More advanced solutions will be considered when supported by concrete performance requirements or functional needs.

---

## 1. Approximate Nearest Neighbor (ANN) Vector Search

**Status:** Planned — Future scalability improvement  
**Priority:** Medium  
**Current solution:** SQLite + NumPy exact similarity search

### Current implementation

The current RAG architecture uses:

1. SQLite to store document chunks and their embeddings as JSON.
2. A multilingual SentenceTransformer model to generate 384-dimensional embeddings.
3. NumPy to compute cosine similarity between the user's query and the stored embeddings.
4. Top-k dense retrieval with a similarity threshold.
5. Cross-Encoder reranking to refine relevance.
6. Maximal Marginal Relevance (MMR) to reduce redundancy in the final context.

The initial retrieval strategy performs an exhaustive similarity search across the embeddings belonging to the selected document or document collection.

For \(N\) embeddings of dimension \(d\), exhaustive similarity computation has a computational cost of approximately \(O(Nd)\) per query, excluding database access and sorting.

This approach is appropriate for small document collections because it is simple, deterministic, and does not require additional infrastructure.

### Proposed improvement

Introduce a vector index based on Approximate Nearest Neighbor (ANN) search.

ANN algorithms are designed to efficiently identify vectors that are likely to be among the nearest neighbors of a query vector, without necessarily computing its similarity against every stored embedding.

Potential technologies include:

- **HNSW:** A graph-based indexing algorithm for approximate nearest neighbor search.

- **pgvector:** A PostgreSQL extension supporting vector similarity search, including approximate indexing methods.

The final technology should be selected according to deployment requirements, dataset size, and operational complexity.

### Advantages

**1. Improved scalability**

ANN indexes can significantly reduce search latency when the number of embeddings becomes large.

**2. Efficient retrieval**

Instead of comparing the query against every embedding, an approximate index can explore a smaller subset of promising candidates.

**3. Better suitability for large document collections**

Vector indexing becomes increasingly useful when the application must search across thousands of documents and potentially hundreds of thousands or millions of chunks.

**4. Preservation of the existing RAG architecture**

The ANN index would replace the candidate-retrieval implementation without necessarily changing Cross-Encoder reranking or MMR.

### Disadvantages and trade-offs

**1. Approximate results**

ANN search generally trades some retrieval accuracy for speed. The index may fail to retrieve one or more of the true nearest neighbors.

**2. Additional complexity**

Building, configuring, updating, and maintaining an index introduces additional implementation and operational requirements.

**3. Memory and storage overhead**

Vector indexes may require additional memory and storage beyond the original embeddings.

**4. Index maintenance**

When documents are inserted, updated, or deleted, the vector index must remain synchronized with the underlying document metadata.

**5. Limited benefits on small datasets**

For a limited number of chunks, exhaustive NumPy similarity search may already be sufficiently fast. ANN indexing may therefore introduce complexity without a meaningful performance improvement.

**6. Retrieval thresholds require careful handling**

An approximate Top-k search may miss relevant embeddings that exceed the configured similarity threshold. In addition, different indexing backends can return distances or similarity scores using different conventions.

### Proposed integration

The future architecture could follow this sequence:

```text
User Query
    |
    v
SentenceTransformer
    |
    v
Query Embedding
    |
    v
ANN Vector Index
    |
    v
Candidate Retrieval (Top-k + Threshold)
    |
    v
Cross-Encoder Reranking
    |
    v
Maximal Marginal Relevance
    |
    v
Selected Context for LLM
    |
    v
Generated Answer
```

Each indexed embedding should remain associated with its document identifier, chunk identifier, page number, and original text.

Whenever possible, the ANN implementation should preserve the existing retrieval interface, allowing the search backend to be replaced without rewriting downstream components.

### When should this improvement be implemented?

ANN indexing should be considered when:

- Document collections grow sufficiently large to cause measurable retrieval latency.
- The application must search across many documents simultaneously.
- Exhaustive similarity search becomes a performance bottleneck.
- Performance benchmarks demonstrate a meaningful benefit from approximate indexing.

Before migrating, the current exact-search implementation should be retained as a baseline for measuring query latency and retrieval quality, including Recall@k.


---

## 2. Improved Document Chunking

### Current limitation

The existing chunking algorithm splits extracted PDF text using fixed character positions.

Consequently, chunks may begin or end in the middle of words or sentences, potentially reducing semantic coherence and retrieval quality.

### Potential improvements

- Split text at word or sentence boundaries.
- Preserve paragraph structure where possible.
- Introduce token-aware chunk sizing.
- Consider recursive text splitting.
- Preserve meaningful structural elements such as section headings and document metadata.

### Trade-offs

More sophisticated chunking may improve contextual coherence, but it introduces additional processing logic and tuning parameters.

Its effectiveness should be evaluated using representative documents and retrieval-quality tests rather than assumed in advance.

### Decision

Evaluate chunking improvements before or during retrieval-quality optimization, while preserving the current chunking implementation as a baseline.



## 3. Configurable LLM Generation Backends


### Current implementation

The RAG system provides a model-independent generation interface.

The initial implementation uses a mock generator to validate
the interaction between document retrieval and answer generation.

This architectural decision is primarily motivated by hardware
constraints and cost considerations.

Running a generative LLM locally would require additional
computational resources and memory, potentially exceeding the
practical capabilities of the development machine.

Alternatively, using external LLM APIs would introduce usage-based
costs, which are intentionally avoided in this personal project.

Therefore, a mock generator is used to develop and test the complete
RAG architecture without requiring additional local inference
resources or paid API calls.

The mock does not produce real AI-generated answers.
However, the modular architecture allows a real LLM backend to
be integrated in the future without modifying the retrieval pipeline.

### Proposed improvements

Introduce interchangeable generation backends:

- Local LLM inference using an open-weight language model.
- Optional remote inference through an API provider.
- Configurable backend selection through environment variables.

### Advantages

- Separation between retrieval and generation logic.
- Easier unit testing through dependency injection.
- Flexibility to switch between model providers.
- No mandatory API costs.
- Possibility of fully local document processing.

### Trade-offs

- Local inference requires CPU or GPU resources.
- Larger language models can consume substantial memory.
- Remote APIs may introduce usage costs.
- Different models may require different prompt formats.
- Generated answers require evaluation for factual grounding
  and citation correctness.



