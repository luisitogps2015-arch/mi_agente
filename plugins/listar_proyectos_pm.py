import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def run(params=None):
    proyectos = []

    if not os.path.exists(PROYECTOS_DIR):
        return {
            "ok": True,
            "total": 0,
            "proyectos": []
        }

    for nombre_carpeta in sorted(os.listdir(PROYECTOS_DIR)):
        ruta = os.path.join(PROYECTOS_DIR, nombre_carpeta)

        if not nombre_carpeta.startswith("proyecto_"):
            continue

        if not os.path.isdir(ruta):
            continue

        metadata_path = os.path.join(ruta, "metadata.json")

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception:
                metadata = {
                    "id": nombre_carpeta,
                    "nombre": nombre_carpeta,
                    "estado": "ERROR_METADATA"
                }
        else:
            metadata = {
                "id": nombre_carpeta,
                "nombre": nombre_carpeta,
                "estado": "SIN_METADATA"
            }

        metadata["ruta"] = ruta
        proyectos.append(metadata)

    return {
        "ok": True,
        "total": len(proyectos),
        "proyectos": proyectos
    }
