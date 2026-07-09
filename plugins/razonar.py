from reasoning_engine import razonar_con_contexto

def run(params):
    query = params.get("query") or params.get("pregunta") or params.get("texto")

    if not query:
        return "Error: falta parámetro query."

    resultado = razonar_con_contexto(query)

    if not resultado.get("ok"):
        return f"Error: {resultado.get('error')}"

    return resultado.get("respuesta", "")
