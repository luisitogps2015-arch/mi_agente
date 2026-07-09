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
    titulo = params.get("titulo", "Acta generada por PM Copilot")
    contenido = params.get("contenido", "").strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido para generar el acta."
        }

    ruta_proyecto = os.path.join(PROYECTOS_DIR, proyecto_id)
    ruta_actas = os.path.join(ruta_proyecto, "actas")

    if not os.path.exists(ruta_proyecto):
        return {
            "ok": False,
            "error": f"El proyecto {proyecto_id} no existe."
        }

    os.makedirs(ruta_actas, exist_ok=True)

    fecha = datetime.utcnow().strftime("%Y_%m_%d_%H%M%S")
    nombre_archivo = f"ACTA_{fecha}_{normalizar_nombre(titulo)}.md"
    ruta_archivo = os.path.join(ruta_actas, nombre_archivo)

    acta = f"""# ACTA DE REUNIÓN

## Título
{titulo}

## Fecha
{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

## Proyecto
{proyecto_id}

---

## Contenido Base Recibido

{contenido}

---

## Temas Tratados

- Pendiente de clasificación automática.
- Pendiente de extracción desde contenido base.

---

## Acuerdos

- Pendiente de identificación automática.

---

## Compromisos

| Responsable | Compromiso | Fecha | Estado |
|---|---|---|---|
| Por definir | Por definir | Por definir | Pendiente |

---

## Riesgos / Alertas

- Pendiente de análisis.

---

## Próximos Pasos

- Revisar acta generada.
- Completar responsables y fechas.
- Validar compromisos.

---

## Generado por
PM Copilot Autónomo
"""

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(acta)

    return {
        "ok": True,
        "mensaje": "Acta PM generada correctamente",
        "proyecto_id": proyecto_id,
        "archivo": nombre_archivo,
        "ruta": ruta_archivo
    }
