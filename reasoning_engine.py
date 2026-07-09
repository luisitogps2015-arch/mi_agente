import json
import os

from groq import Groq
from rag_engine import responder_con_rag


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_REASONING = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)


def razonar_con_contexto(query: str) -> dict:
    if not GROQ_API_KEY:
        return {
            "ok": False,
            "error": "No existe GROQ_API_KEY en variables de entorno."
        }

    rag = responder_con_rag(query)

    if not rag.get("ok"):
        return {
            "ok": False,
            "error": rag.get("error", "No se pudo obtener respuesta RAG"),
            "query": query
        }

    respuesta_rag = rag.get("respuesta", "")
    fuentes = rag.get("fuentes", [])

    prompt = f"""
Actúa como arquitecto técnico de un sistema de agentes IA.

Tu tarea es analizar la respuesta RAG y generar razonamiento controlado.

Pregunta original:
{query}

Respuesta RAG:
{respuesta_rag}

Formato obligatorio:

1. Análisis
Explica qué está ocurriendo técnicamente.

2. Inferencia
Explica qué se puede concluir a partir del contexto.

3. Riesgo o consideración
Indica si hay algún riesgo, dependencia o punto de mejora.

4. Recomendación técnica
Da una recomendación clara y accionable.

Reglas:
- No inventes información fuera de la respuesta RAG.
- No muestres razonamiento oculto ni cadenas internas extensas.
- Sé claro, técnico y directo.
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODELO_REASONING,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un motor de razonamiento controlado para un agente IA. "
                        "Analizas evidencia recuperada por RAG y produces conclusiones técnicas."
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
            "version": "REASONING_V1",
            "query": query,
            "respuesta": respuesta,
            "rag_base": respuesta_rag,
            "fuentes": fuentes
        }

    except Exception as e:
        return {
            "ok": False,
            "version": "REASONING_V1",
            "error": str(e),
            "query": query,
            "fuentes": fuentes
        }


if __name__ == "__main__":
    pregunta = input("Pregunta Reasoning: ").strip()
    salida = razonar_con_contexto(pregunta)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
