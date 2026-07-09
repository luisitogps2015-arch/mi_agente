import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    tipo_filtro = params.get("tipo", "").strip()

    ruta_memoria = os.path.join(PROYECTOS_DIR, proyecto_id, "memoria")
    historial_path = os.path.join(ruta_memoria, "historial.json")
    contexto_path = os.path.join(ruta_memoria, "contexto.md")

    if not os.path.exists(historial_path):
        return {
            "ok": True,
            "proyecto_id": proyecto_id,
            "total": 0,
            "memoria": [],
            "mensaje": "No existe memoria registrada para este proyecto."
        }

    try:
        with open(historial_path, "r", encoding="utf-8") as f:
            historial = json.load(f)
    except Exception as e:
        return {
            "ok": False,
            "error": f"No se pudo leer la memoria del proyecto: {e}"
        }

    if tipo_filtro:
        historial = [
            item for item in historial
            if item.get("tipo") == tipo_filtro
        ]

    ultimos = historial[-10:]

    resumen = []
    for item in ultimos:
        resumen.append({
            "id": item.get("id"),
            "fecha": item.get("fecha"),
            "tipo": item.get("tipo"),
            "contenido": item.get("contenido")
        })

    contexto_disponible = os.path.exists(contexto_path)

    return {
        "ok": True,
        "proyecto_id": proyecto_id,
        "total": len(historial),
        "ultimos": resumen,
        "contexto_md": contexto_path if contexto_disponible else "",
        "mensaje": "Memoria del proyecto consultada correctamente"
    }
