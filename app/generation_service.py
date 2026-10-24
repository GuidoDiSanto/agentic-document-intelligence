from typing import Protocol


class GeneratoreLLM(Protocol):
    #definisce un interfaccia , qualsiasi generatore vogliamo utilizzare 
    # dovrà avere un metodo genera() che riceve una domanda e un contesto e restituisce una stringa.

    def genera(self, domanda: str, contesto: str) -> str:
        ...


class GeneratoreMock:

    def genera(self, domanda: str, contesto: str) -> str:
        return (
            "[MOCK - Nessun LLM reale utilizzato]\n"
            f"Domanda ricevuta: {domanda}\n"
            f"Contesto ricevuto: {len(contesto)} caratteri.\n"
            "Il collegamento con il servizio di generazione funziona."
        )


def recupera_generatore() -> GeneratoreLLM:
    return GeneratoreMock()


def genera_risposta(domanda: str, risultati: list[dict], generatore: GeneratoreLLM) -> str:

    if len(risultati) == 0:
        return "Non sono state trovate informazioni pertinenti."

    parti_contesto = []

    for risultato in risultati:
        pagina = risultato["numero_pagina"]
        testo = risultato["testo"]

        parti_contesto.append(f"[Pagina {pagina}]\n{testo}")

    contesto = "\n\n---\n\n".join(parti_contesto)

    return generatore.genera(domanda, contesto)
