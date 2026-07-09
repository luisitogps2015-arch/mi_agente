import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    contenido = params.get("contenido", "").strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido para generar backlog."
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
    nombre_archivo = f"BACKLOG_{fecha}.md"
    ruta_archivo = os.path.join(ruta_backlog, nombre_archivo)

    backlog = f"""# BACKLOG DEL PROYECTO

## Proyecto
{proyecto_id}

## Fecha
{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Contenido Base Recibido

{contenido}

---

## Épicas Identificadas

| ID | Épica | Descripción | Prioridad |
|---|---|---|---|
| EP-001 | Por definir | Derivada del contenido base | Media |

---

## Historias de Usuario

| ID | Historia | Criterio de Aceptación | Prioridad | Estado |
|---|---|---|---|---|
| HU-001 | Como usuario, quiero convertir la información de reunión en tareas accionables | Dado un texto base, cuando se procese, entonces debe generar tareas iniciales | Media | Pendiente |

---

## Tareas Técnicas / Funcionales

| ID | Tarea | Tipo | Responsable | Estado |
|---|---|---|---|---|
| T-001 | Revisar contenido base y refinar backlog | Funcional | Por definir | Pendiente |

---

## Dependencias

- Pendiente de análisis.

---

## Observaciones

- Backlog generado automáticamente por PM Copilot.
- La clasificación avanzada de épicas, historias y tareas será mejorada en la siguiente iteración.

---

## Generado por
PM Copilot Autónomo
"""

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(backlog)

    return {
        "ok": True,
        "mensaje": "Backlog PM generado correctamente",
        "proyecto_id": proyecto_id,
        "archivo": nombre_archivo,
        "ruta": ruta_archivo
    }
