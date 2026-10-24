import pymupdf


def crea_chunks(pagine: list[dict], dimensione_chunk: int = 500,  overlap: int = 100) -> list[dict]:
    # 1. Crea una lista vuota chiamata chunks
    chunks = []

    if dimensione_chunk <= overlap : 
        raise ValueError("Il valore della dimensione del chunk deve essere maggiore del valore di overlap")
    if dimensione_chunk <= 0 : 
        raise ValueError("Il valore dlela dimensione del chunk deve essere > 0")
    if  overlap < 0: 
        raise ValueError("Il valore di overlap deve essere >= 0")
    # 2. Itera su tutti i dizionari presenti in pagine
    for pagina in pagine: 
        testo = pagina["testo"]
        numero_pagina = pagina["numero_pagina"]
        
        passo = dimensione_chunk - overlap
        for inizio in range(0, len(testo), passo):
            fine = inizio + dimensione_chunk
            chunk = {
                "numero_pagina": numero_pagina,
                "testo" : testo[inizio:fine]
            }
            chunks.append(chunk)
            if fine >= len(testo):
                 break

    
    return chunks
