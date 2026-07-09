from rag_engine import responder_con_rag

def run(params):
    query = params.get("query") or params.get("pregunta") or params.get("texto")

    if not query:
        return "Error: falta parámetro query."

    resultado = responder_con_rag(query)

    if not resultado.get("ok"):
        return f"Error: {resultado.get('error')}"

    respuesta = resultado.get("respuesta", "")
    fuentes = resultado.get("fuentes", [])

    fuentes_txt = "\n".join([
        f"- {f.get('source')} | {f.get('tipo')} | {f.get('nombre')}"
        for f in fuentes
    ])

    return (
        f"{respuesta}\n\n"
        f"FUENTES INTERNAS:\n{fuentes_txt}"
    )
