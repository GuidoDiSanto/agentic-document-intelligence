import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

def similarita_coseno(a: np.ndarray, b: np.ndarray) -> float:
    '''
    Calcolare il prodotto scalare di a e b.
    Calcolare la norma di ciascun vettore.
    Controllare che nessuna delle due norme sia zero; in quel caso solleva ValueError.
    Applicare la formula della cosine similarity.
    Restituire il risultato come float.
    '''
    prod = np.dot(a,b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        raise ValueError("I vettori devono avere norma diversa da 0")
    
    cos_similarity = float(prod / (norm_a * norm_b))
    return cos_similarity


def recupera_candidati_dense(domanda: str, chunks: list[dict], embeddings: np.ndarray, modello: SentenceTransformer, top_n: int = 8, soglia: float = 0.3) -> list[dict]:
    '''
    Genera l'embedding della domanda attraverso modello.encode(domanda).
    Calcola la similarità coseno tra la domanda e ogni riga della matrice embeddings.
    Ordina gli indici dei chunk in ordine decrescente di similarità, usando np.argsort().
    Seleziona al massimo top_n indici.
    Per ciascuno, verifica che la similarità sia almeno soglia.
    Costruisci il dizionario con indice, numero_pagina, testo e dense_score.
    Restituisci la lista dei candidati.
    '''
    if top_n <= 0:
        raise ValueError("top_n deve essere maggiore di zero")

    if len(chunks) != len(embeddings):
        raise ValueError("Il numero di chunk e embeddings deve coincidere")

    if len(chunks) == 0:
        return []
    
    dom_embedded = modello.encode(domanda)
    similarity_score = []
    for embedding in embeddings:
        similarity = similarita_coseno(dom_embedded, embedding)
        similarity_score.append(similarity)

    # [::1] ordine decrescente , [:top_n] solo le prime top_n
    indici_ordinati = np.argsort(similarity_score)[::-1][:top_n]
    candidati = []

    for indice in indici_ordinati:
        score = similarity_score[indice]
        if score < soglia:
            continue
            # ovvero se score < soglia ignora questo chunk e passa al successivo
        chunk = chunks[indice]
        candidato = {
            "indice": int(indice),
            "numero_pagina": chunk["numero_pagina"],
            "testo": chunk["testo"],
            "dense_score": float(score)
        }
        candidati.append(candidato)

    return candidati
       

def reranka_candidati(domanda: str, candidati: list[dict], reranker: CrossEncoder) -> list[dict]:
    '''
    Se candidati è vuota, restituire immediatamente [].
    Costruire le coppie (domanda, candidato["testo"]) per ogni candidato.
    Chiamare reranker.predict() con batch_size=2.
    Attraversare candidati e punteggi con zip(), aggiungendo a ciascun candidato il campo "rerank_score" come float.
    Restituire i candidati ordinati in senso decrescente in base a "rerank_score".
    '''
    if len(candidati) == 0:
        return []
    
    coppie = []
    for candidato in candidati: 
        coppia = (domanda, candidato["testo"])
        coppie.append(coppia)

    punteggi = reranker.predict(coppie, batch_size=2)

    for candidato, punteggio in zip(candidati, punteggi):
        candidato["rerank_score"] = float(punteggio)

    ordinati = sorted(
        candidati,
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return ordinati

def seleziona_mmr(candidati: list[dict], embeddings: np.ndarray, k: int = 3, lambda_mmr: float = 0.7) -> list[dict]:
    '''
    Controlla che k > 0 e che lambda_mmr sia compreso tra 0 e 1. Se i candidati sono vuoti, restituisci [].
    Normalizza i punteggi rerank_score tramite Min-Max e salva il risultato in rilevanza_norm.
    Crea selezionati e rimanenti, poi seleziona il primo candidato (il più rilevante).
    Utilizza while per continuare finché hai selezionato k chunk oppure hai esaurito i candidati.
    Per ogni candidato rimanente, confronta il suo embedding con quelli di tutti i chunk già selezionati e calcola la ridondanza massima normalizzata.
    Calcola il punteggio MMR con lambda_mmr=0.7.
    Seleziona il candidato con il punteggio MMR maggiore, aggiungilo a selezionati e rimuovilo da rimanenti.
    Restituisci selezionati.
    '''
    if k <= 0: 
        raise ValueError("k deve essere maggiore di zero")
    if lambda_mmr < 0 or lambda_mmr > 1:
        raise ValueError("Lambdra deve essere compresa tra 0 e 1")
    if len(candidati) == 0:
        return []
    
    punteggi = []
    for candidato in candidati:
        punteggio = candidato["rerank_score"]
        punteggi.append(punteggio)

    min_score = min(punteggi)
    max_score = max(punteggi)

    for candidato in candidati:
        if max_score == min_score:
            rilevanza_norm = 1.0
        else:
            rilevanza_norm = (candidato["rerank_score"] - min_score) / (max_score - min_score)
            candidato["rilevanza_norm"] = rilevanza_norm

    selezionati = []
    rimanenti = candidati.copy()
    
    primo = rimanenti.pop(0)
    selezionati.append(primo)

    while len(selezionati) < k and rimanenti:
        migliore = None
        miglior_punteggio = float("-inf")

        for candidato in rimanenti:
            similarita = []

            for selezionato in selezionati:
                embedding_candidato = embeddings[candidato["indice"]]
                embedding_selezionato = embeddings[selezionato["indice"]]
                similarity = similarita_coseno(
                    embedding_candidato,
                    embedding_selezionato
                )
                similarita.append(similarity)

            ridondanza_massima = max(similarita)
            ridondanza_norm = (ridondanza_massima + 1) / 2

            punteggio_mmr = ( lambda_mmr * candidato["rilevanza_norm"] - (1 - lambda_mmr) * ridondanza_norm)

            if punteggio_mmr > miglior_punteggio:
                miglior_punteggio = punteggio_mmr
                migliore = candidato

        selezionati.append(migliore)
        rimanenti.remove(migliore)

    return selezionati



def retrieval_completo(
    domanda: str,
    chunks: list[dict],
    embeddings: np.ndarray,
    modello: SentenceTransformer,
    reranker: CrossEncoder,
    top_n: int = 8,
    soglia: float = 0.3,
    k: int = 3,
    lambda_mmr: float = 0.7
) -> list[dict]:

    candidati = recupera_candidati_dense(
        domanda,
        chunks,
        embeddings,
        modello,
        top_n=top_n,
        soglia=soglia
    )

    if len(candidati) == 0:
        return []

    candidati = reranka_candidati(
        domanda,
        candidati,
        reranker
    )

    risultati = seleziona_mmr(
        candidati,
        embeddings,
        k=k,
        lambda_mmr=lambda_mmr
    )

    return risultati
