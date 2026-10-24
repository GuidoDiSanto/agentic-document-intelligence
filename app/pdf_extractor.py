import pymupdf
from fastapi import Query

def estrai_pagine_pdf(percorso_file: str) -> list[dict]:
    # 1. Crea una lista vuota chiamata pagine_estratte
    pagine_estratte = []
    # 2. Apri il documento utilizzando with
    with pymupdf.open(percorso_file) as pdf:
        for numero, pagina in enumerate(pdf, start=1):
            # print(numero)
            testo = pagina.get_text("text")
            dati_pagina={
                "numero_pagina": numero,
                "testo" : testo
            }
            pagine_estratte.append(dati_pagina)
        
        return pagine_estratte