from functools import lru_cache
from sentence_transformers import SentenceTransformer, CrossEncoder


@lru_cache(maxsize=1)
def recupera_modello_embedding() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device="cpu"
    )


@lru_cache(maxsize=1)
def recupera_modello_reranker() -> CrossEncoder:
    return CrossEncoder(
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        device="cpu"
    )
