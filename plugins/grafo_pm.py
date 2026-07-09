from pm_langgraph import ejecutar_pm_graph


def run(params=None):
    params = params or {}

    ruta = params.get("ruta", "").strip()
    proyecto_id = params.get("proyecto_id", "proyecto_001")

    if not ruta:
        return {
            "ok": False,
            "error": "No se recibió ruta para ejecutar el grafo PM."
        }

    resultado = ejecutar_pm_graph(
        ruta,
        proyecto_id
    )

    return {
        "ok": resultado.get("estado") == "DELIVERY_COMPLETED",
        "mensaje": "Grafo PM ejecutado correctamente",
        "estado_final": resultado.get("estado"),
        "resultado": resultado
    }
