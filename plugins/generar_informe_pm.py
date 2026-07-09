import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    titulo = params.get("titulo", "Informe Ejecutivo generado por PM Copilot")
    contenido = params.get("contenido", "").strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido para generar informe ejecutivo."
        }

    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)
    ruta_informes = os.path.join(ruta_proyecto, "informes")

    if not os.path.exists(ruta_proyecto):
        return {
            "ok": False,
            "error": f"El proyecto {proyecto_id} no existe."
        }

    os.makedirs(ruta_informes, exist_ok=True)

    fecha = datetime.utcnow().strftime("%Y_%m_%d_%H%M%S")
    nombre_archivo = f"INFORME_EJECUTIVO_{fecha}.md"
    ruta_archivo = os.path.join(ruta_informes, nombre_archivo)

    informe = f"""# INFORME EJECUTIVO DEL PROYECTO

## Título
{titulo}

## Proyecto
{proyecto_id}

## Fecha
{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Resumen Ejecutivo

El proyecto presenta avances relacionados con el contenido base recibido. Este informe consolida el estado general, riesgos, avances, bloqueantes y próximos pasos.

---

## Contenido Base Analizado

{contenido}

---

## Estado General

| Indicador | Estado |
|---|---|
| Avance funcional | En evaluación |
| Riesgos | Identificados |
| Bloqueantes | Por validar |
| Próximos pasos | Definidos parcialmente |

---

## Avances Identificados

- Se recibió información base del proyecto.
- Se identificaron elementos para seguimiento.
- Se generó un informe ejecutivo inicial.
- Se recomienda complementar con acta, compromisos y backlog.

---

## Riesgos / Alertas

- Requerimientos incompletos o ambiguos.
- Falta de responsables definidos.
- Dependencias no documentadas.
- Fechas objetivo no confirmadas.

---

## Próximos Pasos

1. Validar el contenido base con los interesados.
2. Generar o actualizar acta de reunión.
3. Extraer compromisos.
4. Actualizar backlog.
5. Revisar matriz de riesgos.
6. Definir seguimiento en próxima reunión.

---

## Recomendación del PM Copilot

Mantener trazabilidad entre actas, compromisos, backlog, riesgos e informes para fortalecer el control del proyecto.

---

## Generado por
PM Copilot Autónomo
"""

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(informe)

    return {
        "ok": True,
        "mensaje": "Informe ejecutivo PM generado correctamente",
        "proyecto_id": proyecto_id,
        "archivo": nombre_archivo,
        "ruta": ruta_archivo
    }
