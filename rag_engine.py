import json
import os

from dotenv import load_dotenv
from groq import Groq
from context_builder import construir_prompt_rag


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_RAG = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)


def responder_con_rag(query: str) -> dict:
    if not GROQ_API_KEY:
        return {
            "ok": False,
            "error": "No existe GROQ_API_KEY en variables de entorno."
        }

    data = construir_prompt_rag(query, top_k=5)

    if not data.get("ok"):
        return {
            "ok": False,
            "error": data.get("error", "No se pudo construir el prompt RAG")
        }

    prompt_base = data.get("prompt", "")
    fuentes = data.get("fuentes", [])

    prompt_v2 = f"""
Responde como arquitecto técnico del Agente IA.

Usa SOLO el contexto recuperado.

Formato obligatorio:

1. Respuesta corta
Explica la respuesta en 2 o 3 líneas.

2. Explicación técnica
Explica cómo funciona internamente.

3. Evidencia encontrada
Menciona archivo, función o chunk relevante.

4. Conclusión
Resume por qué esto es importante dentro de la arquitectura MCP.

Pregunta:
{query}

Contexto:
{prompt_base}
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODELO_RAG,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un arquitecto técnico especializado en agentes IA, "
                        "MCP, RAG, plugins y orquestación. "
                        "No inventes información fuera del contexto recuperado."
                    )
                },
                {
                    "role": "user",
                    "content": prompt_v2
                }
            ],
            temperature=0.0
        )

        respuesta = response.choices[0].message.content or ""

        return {
            "ok": True,
            "version": "RAG_V2",
            "query": query,
            "respuesta": respuesta,
            "fuentes": fuentes
        }

    except Exception as e:
        return {
            "ok": False,
            "version": "RAG_V2",
            "error": str(e),
            "query": query,
            "fuentes": fuentes
        }


if __name__ == "__main__":
    pregunta = input("Pregunta RAG: ").strip()
    salida = responder_con_rag(pregunta)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
