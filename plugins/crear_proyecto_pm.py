import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def generar_id_proyecto():
    os.makedirs(PROYECTOS_DIR, exist_ok=True)

    existentes = [
        d for d in os.listdir(PROYECTOS_DIR)
        if d.startswith("proyecto_") and os.path.isdir(os.path.join(PROYECTOS_DIR, d))
    ]

    numeros = []
    for item in existentes:
        try:
            numeros.append(int(item.replace("proyecto_", "")))
        except Exception:
            pass

    siguiente = max(numeros) + 1 if numeros else 1
    return f"proyecto_{siguiente:03d}"


def run(params=None):
    params = params or {}

    nombre = params.get("nombre", "Proyecto sin nombre")
    descripcion = params.get("descripcion", "Proyecto creado desde PM Copilot")

    proyecto_id = generar_id_proyecto()
    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)

    carpetas = [
        "actas",
        "minutas",
        "backlog",
        "informes",
        "riesgos",
        "roadmap",
        "documentos",
        "memoria"
    ]

    os.makedirs(ruta_proyecto, exist_ok=True)

    for carpeta in carpetas:
        os.makedirs(os.path.join(ruta_proyecto, carpeta), exist_ok=True)

    metadata = {
        "id": proyecto_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "estado": "ACTIVO",
        "fecha_creacion": datetime.utcnow().isoformat() + "Z",
        "estructura": carpetas
    }

    metadata_path = os.path.join(ruta_proyecto, "metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return {
        "ok": True,
        "mensaje": "Proyecto PM creado correctamente",
        "proyecto": metadata,
        "ruta": ruta_proyecto
    }
