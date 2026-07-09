import json
import os

from groq import Groq
from executor_engine import ejecutar_plan


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_CRITIC = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)


def evaluar_ejecucion(objetivo: str) -> dict:
    if not GROQ_API_KEY:
        return {
            "ok": False,
            "error": "No existe GROQ_API_KEY en variables de entorno."
        }

    ejecucion = ejecutar_plan(objetivo)

    resultados = ejecucion.get("resultados", [])
    estado_final = ejecucion.get("estado_final", "DESCONOCIDO")

    prompt = f"""
Actúa como Critic Agent de mi framework MCP.

Tu trabajo es evaluar si la ejecución cumplió realmente el objetivo.

Objetivo original:
{objetivo}

Estado de ejecución:
{estado_final}

Resultados del Executor:
{json.dumps(resultados, indent=2, ensure_ascii=False)}

Criterios:
- No basta con que el archivo exista.
- No basta con que la sintaxis sea válida.
- Evalúa si el resultado cumple funcionalmente el objetivo.
- Si un plugin dice "Pendiente implementar lógica real", entonces NO cumple totalmente.
- Si quedaron pasos manuales, indica que la ejecución es parcial.
- Si hay fallos, explica cuál es el bloqueo.

Formato obligatorio:

1. Veredicto
Usa uno de estos valores:
CUMPLE | CUMPLE_PARCIALMENTE | NO_CUMPLE

2. Evidencia
Explica qué resultados sustentan el veredicto.

3. Problema principal
Indica el principal faltante o fallo.

4. Recomendación
Indica el siguiente paso técnico.

5. Riesgo
Indica qué riesgo existe si se considera completado sin corregir.
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODELO_CRITIC,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un agente crítico de calidad. "
                        "Evalúas resultados de ejecución de forma estricta y técnica."
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
            "version": "CRITIC_V1",
            "objetivo": objetivo,
            "estado_executor": estado_final,
            "evaluacion": respuesta,
            "ejecucion": ejecucion
        }

    except Exception as e:
        return {
            "ok": False,
            "version": "CRITIC_V1",
            "error": str(e),
            "objetivo": objetivo,
            "ejecucion": ejecucion
        }


if __name__ == "__main__":
    objetivo = input("Objetivo a evaluar: ").strip()
    salida = evaluar_ejecucion(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))

