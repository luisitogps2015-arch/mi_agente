import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def leer_archivos_md(carpeta, limite=5):
    if not os.path.exists(carpeta):
        return []

    archivos = [
        f for f in os.listdir(carpeta)
        if f.endswith(".md")
    ]

    archivos = sorted(archivos)[-limite:]
    resultado = []

    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()[:3000]
            resultado.append({
                "archivo": archivo,
                "contenido": contenido
            })
        except Exception:
            pass

    return resultado


def run(params=None):
    params = params or {}
    proyecto_id = params.get("proyecto_id", "proyecto_001")

    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)

    if not os.path.exists(ruta_proyecto):
        return {
            "ok": False,
            "error": f"El proyecto {proyecto_id} no existe."
        }

    metadata_path = os.path.join(ruta_proyecto, "metadata.json")
    memoria_dir = os.path.join(ruta_proyecto, "memoria")
    os.makedirs(memoria_dir, exist_ok=True)

    metadata = {}

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    contexto_path = os.path.join(memoria_dir, "contexto_general.md")

    secciones = {
        "Actas": leer_archivos_md(os.path.join(ruta_proyecto, "actas")),
        "Backlog / Compromisos": leer_archivos_md(os.path.join(ruta_proyecto, "backlog")),
        "Riesgos": leer_archivos_md(os.path.join(ruta_proyecto, "riesgos")),
        "Informes": leer_archivos_md(os.path.join(ruta_proyecto, "informes")),
        "Roadmap": leer_archivos_md(os.path.join(ruta_proyecto, "roadmap")),
    }

    contenido = f"""# CONTEXTO GENERAL DEL PROYECTO

## Proyecto
{metadata.get("nombre", proyecto_id)}

## ID
{metadata.get("id", proyecto_id)}

## Estado
{metadata.get("estado", "SIN_ESTADO")}

## Fecha de actualización
{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Descripción

{metadata.get("descripcion", "Sin descripción registrada.")}

---

"""

    for nombre_seccion, archivos in secciones.items():
        contenido += f"\n# {nombre_seccion}\n\n"

        if not archivos:
            contenido += "Sin registros disponibles.\n\n"
            continue

        for item in archivos:
            contenido += f"## Archivo: {item['archivo']}\n\n"
            contenido += item["contenido"]
            contenido += "\n\n---\n\n"

    with open(contexto_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    return {
        "ok": True,
        "mensaje": "Contexto general del proyecto actualizado correctamente",
        "proyecto_id": proyecto_id,
        "ruta": contexto_path
    }
