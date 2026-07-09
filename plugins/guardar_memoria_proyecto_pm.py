import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    tipo = params.get("tipo", "nota")
    contenido = params.get("contenido", "").strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido para guardar en memoria."
        }

    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)
    ruta_memoria = os.path.join(ruta_proyecto, "memoria")

    if not os.path.exists(ruta_proyecto):
        return {
            "ok": False,
            "error": f"El proyecto {proyecto_id} no existe."
        }

    os.makedirs(ruta_memoria, exist_ok=True)

    memoria_path = os.path.join(ruta_memoria, "historial.json")

    if os.path.exists(memoria_path):
        try:
            with open(memoria_path, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = []
    else:
        historial = []

    evento = {
        "id": f"mem_{len(historial) + 1:04d}",
        "fecha": datetime.utcnow().isoformat() + "Z",
        "tipo": tipo,
        "contenido": contenido
    }

    historial.append(evento)

    with open(memoria_path, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

    contexto_path = os.path.join(ruta_memoria, "contexto.md")

    with open(contexto_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n## {evento['fecha']} - {tipo}\n\n{contenido}\n")

    return {
        "ok": True,
        "mensaje": "Memoria del proyecto guardada correctamente",
        "proyecto_id": proyecto_id,
        "evento": evento,
        "ruta_json": memoria_path,
        "ruta_contexto": contexto_path
    }
