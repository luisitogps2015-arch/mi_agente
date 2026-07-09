from planner_engine import crear_plan

def run(params):
    objetivo = params.get("objetivo") or params.get("query") or params.get("texto")

    if not objetivo:
        return "Error: falta parámetro objetivo."

    resultado = crear_plan(objetivo)

    if not resultado.get("ok"):
        return f"Error: {resultado.get('error')}"

    return resultado.get("plan", "")
