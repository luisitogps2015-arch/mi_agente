import json
import os

from groq import Groq
from rag_engine import responder_con_rag


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_PLANNER = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)


ARQUITECTURA_REAL = """
Arquitectura real del framework:

Telegram
↓
app.py
↓
mcp_server.py
↓
agent_loop.py
↓
mcp_client.py
↓
plugin_registry.py
↓
plugins

Reglas reales del sistema:
- Los plugins viven en la carpeta plugins/.
- Cada plugin debe ser un archivo .py.
- Cada plugin debe tener función run(params).
- NO se crean archivos metadata .json para plugins.
- plugin_registry.py detecta plugins automáticamente.
- NO se debe modificar plugin_registry.py para registrar un plugin.
- La activación se hace agregando el nombre del plugin en plugins_activos.json.
- La validación inicial se hace con python3 -m py_compile plugins/nombre_plugin.py.
- La prueba directa se hace con plugin_registry.run_plugin.
- Si el comando debe entenderse por texto, se agrega una regla en mcp_client.py.
- La prueba de flujo se hace con agent_loop.py.
- Si se probará desde Telegram/Docker, se hace rebuild de Docker.
"""


def crear_plan(objetivo: str) -> dict:
    if not GROQ_API_KEY:
        return {
            "ok": False,
            "error": "No existe GROQ_API_KEY en variables de entorno."
        }

    rag = responder_con_rag(objetivo)

    contexto_base = ""
    fuentes = []

    if rag.get("ok"):
        contexto_base = rag.get("respuesta", "")
        fuentes = rag.get("fuentes", [])

    prompt = f"""
Actúa como Planner técnico de MI framework de agentes IA.

Debes crear un plan usando estrictamente la arquitectura real descrita.

{ARQUITECTURA_REAL}

Objetivo del usuario:
{objetivo}

Contexto recuperado por RAG:
{contexto_base}

Formato obligatorio:

1. Objetivo interpretado
Explica qué se quiere lograr en una frase.

2. Plan de ejecución real
Lista pasos numerados, concretos y accionables.

3. Archivos o componentes involucrados
Menciona solo componentes reales de esta arquitectura.

4. Validaciones necesarias
Incluye comandos o pruebas esperadas cuando aplique.

5. Riesgos o precauciones
Indica qué puede fallar y cómo evitarlo.

Reglas estrictas:
- NO digas que hay que registrar manualmente el plugin en plugin_registry.py.
- NO digas que hay que modificar plugin_registry.py salvo que el objetivo sea cambiar el registry.
- NO crees archivos metadata .json para plugins.
- Para crear plugins, usa solo plugins/nombre_plugin.py.
- Para activar plugins, usa plugins_activos.json.
- Para validar sintaxis, usa python3 -m py_compile plugins/nombre_plugin.py.
- Para probar plugin directo, usa:
  python3 -c "from plugin_registry import run_plugin; print(run_plugin('nombre_plugin', {{}}))"
- Para probar flujo completo, usa agent_loop.py.
- Para Telegram, indicar rebuild Docker.
- No ejecutes nada, solo planifica.
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODELO_PLANNER,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres el Planner técnico de un framework MCP propio. "
                        "Tus planes deben respetar exactamente la arquitectura real "
                        "y evitar pasos genéricos, metadata innecesaria o instrucciones incorrectas."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0
        )

        respuesta = response.choices[0].message.content or ""

        return {
            "ok": True,
            "version": "PLANNER_V2_1",
            "objetivo": objetivo,
            "plan": respuesta,
            "fuentes": fuentes
        }

    except Exception as e:
        return {
            "ok": False,
            "version": "PLANNER_V2_1",
            "error": str(e),
            "objetivo": objetivo,
            "fuentes": fuentes
        }


if __name__ == "__main__":
    objetivo = input("Objetivo para planificar: ").strip()
    salida = crear_plan(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
