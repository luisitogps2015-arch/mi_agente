from goal_manager import obtener_objetivo
from orchestrator_engine import orquestar


def run(params):
    goal_id = (
        params.get("id")
        or params.get("goal_id")
        or ""
    ).strip()

    if not goal_id:
        return "Error: falta el ID del objetivo."

    resultado = obtener_objetivo(goal_id)

    if not resultado.get("ok"):
        return resultado.get(
            "error",
            "Objetivo no encontrado."
        )

    goal = resultado.get("goal", {})

    objetivo = goal.get("objetivo", "").strip()

    if not objetivo:
        return "Error: el objetivo está vacío."

    salida = orquestar(objetivo)

    return (
        f"Objetivo reanudado: {goal_id}\n"
        f"Objetivo: {objetivo}\n"
        f"Estado final: {salida.get('estado_final')}"
    )
