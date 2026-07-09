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
            "error": "No se recibió contenido para generar riesgos."
        }

    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)
    ruta_riesgos = os.path.join(ruta_proyecto, "riesgos")

    if not os.path.exists(ruta_proyecto):
        return {
            "ok": False,
            "error": f"El proyecto {proyecto_id} no existe."
        }

    os.makedirs(ruta_riesgos, exist_ok=True)

    fecha = datetime.utcnow().strftime("%Y_%m_%d_%H%M%S")
    nombre_archivo = f"RIESGOS_{fecha}.md"
    ruta_archivo = os.path.join(ruta_riesgos, nombre_archivo)

    riesgos = f"""# MATRIZ DE RIESGOS DEL PROYECTO

## Proyecto
{proyecto_id}

## Fecha
{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Contenido Base Analizado

{contenido}

---

## Riesgos Identificados

| ID | Riesgo | Impacto | Probabilidad | Nivel | Mitigación | Estado |
|---|---|---|---|---|---|---|
| R-001 | Requerimientos incompletos o ambiguos | Alto | Media | Alto | Validar alcance con interesados antes de ejecutar | Abierto |
| R-002 | Retrasos por dependencias externas | Medio | Media | Medio | Identificar dependencias y responsables | Abierto |
| R-003 | Falta de validación del usuario final | Alto | Baja | Medio | Programar revisión funcional temprana | Abierto |

---

## Alertas para el PM

- Revisar si existen fechas comprometidas.
- Confirmar responsables de cada actividad.
- Validar dependencias antes de iniciar desarrollo.
- Actualizar esta matriz después de cada reunión importante.

---

## Recomendación

Convertir los riesgos críticos en acciones preventivas dentro del backlog del proyecto.

---

## Generado por
PM Copilot Autónomo
"""

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(riesgos)

    return {
        "ok": True,
        "mensaje": "Matriz de riesgos PM generada correctamente",
        "proyecto_id": proyecto_id,
        "archivo": nombre_archivo,
        "ruta": ruta_archivo
    }
