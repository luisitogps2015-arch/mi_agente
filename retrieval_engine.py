from search_engine import buscar


def recuperar_contexto(query, limite=3):

    resultados = buscar(query)

    contexto = []

    for r in resultados[:limite]:

        contexto.append(
            r.get("contenido", "")
        )

    return {
        "query": query,
        "total": len(contexto),
        "contexto": contexto
    }


if __name__ == "__main__":

    query = input("Consulta: ")

    resultado = recuperar_contexto(query)

    import json

    print(
        json.dumps(
            resultado,
            indent=2,
            ensure_ascii=False
        )
    )
