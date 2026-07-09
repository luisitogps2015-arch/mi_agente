from context_builder import construir_contexto

def run(params):
    query = params.get("query") or params.get("pregunta") or params.get("texto")

    if not query:
        return "Error: falta parámetro query."

    resultado = construir_contexto(query, top_k=5)

    if not resultado.get("ok"):
        return f"Error: {resultado.get('error')}"

    if not resultado.get("contexto"):
        return "No se encontró contexto relevante."

    return resultado.get("contexto")
