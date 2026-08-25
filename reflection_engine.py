import json
import os

from groq import Groq
from critic_engine import evaluar_ejecucion


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_REFLECTION = "openai/gpt-oss-20b"

client = Groq(api_key=GROQ_API_KEY)


def generar_reflexion(objetivo: str) -> dict:
    if not GROQ_API_KEY:
        return {
            "ok": False,
            "error": "No existe GROQ_API_KEY en variables de entorno."
        }

    critica = evaluar_ejecucion(objetivo)

    if not critica.get("ok"):
        return {
            "ok": False,
            "error": critica.get("error", "No se pudo evaluar ejecución."),
            "objetivo": objetivo
        }

    evaluacion = critica.get("evaluacion", "")
    ejecucion = critica.get("ejecucion", {})

    prompt = f"""
Actúa como Reflection Agent de mi framework MCP.

Tu tarea es convertir la crítica de ejecución en aprendizaje y próximos pasos.

Objetivo original:
{objetivo}

Crítica:
{evaluacion}

Resultado de ejecución:
{json.dumps(ejecucion, indent=2, ensure_ascii=False)}

Formato obligatorio:

1. Qué salió bien
Lista lo que funcionó correctamente.

2. Qué falló o quedó incompleto
Lista lo que no cumplió el objetivo.

3. Aprendizaje
Explica qué debe recordar el sistema para próximas ejecuciones similares.

4. Próxima acción recomendada
Indica la acción técnica inmediata para avanzar.

5. Candidato para Self-Healing
Indica si este caso debe pasar a autocuración:
SI | NO

Reglas:
- No inventes resultados.
- Usa la crítica como fuente principal.
- Sé directo y accionable.
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODELO_REFLECTION,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un agente de reflexión para un framework MCP. "
                        "Tu función es convertir errores y ejecuciones parciales "
                        "en aprendizaje accionable."
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
            "version": "REFLECTION_V1",
            "objetivo": objetivo,
            "reflexion": respuesta,
            "critica": critica
        }

    except Exception as e:
        return {
            "ok": False,
            "version": "REFLECTION_V1",
            "error": str(e),
            "objetivo": objetivo,
            "critica": critica
        }


if __name__ == "__main__":
    objetivo = input("Objetivo para reflexionar: ").strip()
    salida = generar_reflexion(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))

