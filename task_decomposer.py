import json
import os
import re

from groq import Groq
from planner_engine import crear_plan


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_DECOMPOSER = "openai/gpt-oss-20b"

client = Groq(api_key=GROQ_API_KEY)


def extraer_json(texto: str):
    """
    Intenta extraer un JSON válido desde la respuesta del modelo.
    """
    try:
        return json.loads(texto)
    except Exception:
        pass

    match = re.search(r"\[.*\]", texto, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    return None


def descomponer_tareas(objetivo: str) -> dict:
    if not GROQ_API_KEY:
        return {
            "ok": False,
            "error": "No existe GROQ_API_KEY en variables de entorno."
        }

    plan = crear_plan(objetivo)

    if not plan.get("ok"):
        return {
            "ok": False,
            "error": plan.get("error", "No se pudo crear plan"),
            "objetivo": objetivo
        }

    plan_texto = plan.get("plan", "")

    prompt = f"""
Actúa como Task Decomposer de mi framework MCP.

Tu trabajo es convertir un plan técnico en una lista JSON de tareas ejecutables.

Arquitectura real:
- Plugins en plugins/nombre_plugin.py
- Cada plugin debe tener run(params)
- Activación en plugins_activos.json
- Validación con python3 -m py_compile
- Prueba directa con plugin_registry.run_plugin
- Prueba completa con agent_loop.py
- Rebuild Docker solo si se probará desde Telegram

Objetivo:
{objetivo}

Plan generado:
{plan_texto}

Devuelve SOLO un JSON válido, sin markdown, sin explicación.

Formato requerido:
[
  {{
    "orden": 1,
    "tarea": "descripción corta",
    "accion": "crear_archivo | validar_sintaxis | activar_plugin | probar_plugin | actualizar_mcp_client | probar_agent_loop | rebuild_docker | verificacion_manual",
    "archivo": "ruta si aplica",
    "plugin": "nombre si aplica",
    "comando": "comando sugerido si aplica",
    "estado": "pendiente"
  }}
]

Reglas:
- No inventes archivos .json metadata para plugins.
- No modifiques plugin_registry.py salvo que el objetivo sea modificar el registry.
- Usa plugins_activos.json para activar plugins.
- Mantén entre 4 y 8 tareas.
- Cada tarea debe ser clara y ejecutable.
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODELO_DECOMPOSER,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un descomponedor de tareas para un framework MCP. "
                        "Tu salida debe ser JSON válido únicamente."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0
        )

        texto = response.choices[0].message.content or ""
        tareas = extraer_json(texto)

        if tareas is None:
            return {
                "ok": False,
                "error": "No se pudo extraer JSON válido.",
                "raw": texto,
                "objetivo": objetivo
            }

        return {
            "ok": True,
            "version": "TASK_DECOMPOSER_V1",
            "objetivo": objetivo,
            "tareas": tareas,
            "plan_base": plan_texto
        }

    except Exception as e:
        return {
            "ok": False,
            "version": "TASK_DECOMPOSER_V1",
            "error": str(e),
            "objetivo": objetivo
        }


if __name__ == "__main__":
    objetivo = input("Objetivo para descomponer: ").strip()
    salida = descomponer_tareas(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
