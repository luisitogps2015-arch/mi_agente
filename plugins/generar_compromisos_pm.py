import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def normalizar_nombre(texto):
    limpio = "".join(c if c.isalnum() else "_" for c in texto.lower())
    return "_".join(limpio.split("_"))[:60]


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    contenido = params.get("contenido", "").strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido para generar compromisos."
        }

    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)
    ruta_backlog = os.path.join(ruta_proyecto, "backlog")

    if not os.path.exists(ruta_proyecto):
        return {
            "ok": False,
            "error": f"El proyecto {proyecto_id} no existe."
        }

    os.makedirs(ruta_backlog, exist_ok=True)

    fecha = datetime.utcnow().strftime("%Y_%m_%d_%H%M%S")
    nombre_archivo = f"COMPROMISOS_{fecha}.md"
    ruta_archivo = os.path.join(ruta_backlog, nombre_archivo)

    compromisos = f"""# COMPROMISOS DEL PROYECTO

## Proyecto
{proyecto_id}

## Fecha
{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Contenido Base Recibido

{contenido}

---

## Compromisos Identificados

| ID | Responsable | Compromiso | Fecha Objetivo | Estado |
|---|---|---|---|---|
| C-001 | Por definir | Revisar contenido base y completar compromiso | Por definir | Pendiente |

---

## Observaciones

- Este archivo fue generado automáticamente por PM Copilot.
- La extracción inteligente de responsables y fechas será mejorada en la siguiente iteración.
- Este documento puede usarse como base para seguimiento de reunión.

---

## Generado por
PM Copilot Autónomo
"""

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(compromisos)

    return {
        "ok": True,
        "mensaje": "Compromisos PM generados correctamente",
        "proyecto_id": proyecto_id,
        "archivo": nombre_archivo,
        "ruta": ruta_archivo
    }
