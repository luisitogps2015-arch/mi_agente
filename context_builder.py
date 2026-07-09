import json
from retrieval_manager import buscar_contexto_hibrido


def construir_contexto(query, top_k=5, max_chars=4000):
    resultado = buscar_contexto_hibrido(query, top_k=top_k)

    if not resultado.get("ok"):
        return {
            "ok": False,
            "error": resultado.get("error", "Error construyendo contexto")
        }

    chunks = resultado.get("resultados", [])

    if not chunks:
        return {
            "ok": True,
            "query": query,
            "contexto": "",
            "fuentes": [],
            "mensaje": "No se encontraron chunks relevantes."
        }

    partes = []
    fuentes = []
    total_chars = 0

    for i, chunk in enumerate(chunks, start=1):
        contenido = chunk.get("content", "").strip()

        if not contenido:
            continue

        bloque = (
            f"\n--- CONTEXTO {i} ---\n"
            f"Fuente: {chunk.get('source')}\n"
            f"Tipo: {chunk.get('tipo')}\n"
            f"Nombre: {chunk.get('nombre')}\n"
            f"Chunk ID: {chunk.get('chunk_id')}\n"
            f"Score: {chunk.get('rerank_score')}\n\n"
            f"{contenido}\n"
        )

        if total_chars + len(bloque) > max_chars:
            break

        partes.append(bloque)
        total_chars += len(bloque)

        fuentes.append({
            "chunk_id": chunk.get("chunk_id"),
            "source": chunk.get("source"),
            "tipo": chunk.get("tipo"),
            "nombre": chunk.get("nombre"),
            "score": chunk.get("rerank_score")
        })

    contexto = "\n".join(partes)

    return {
        "ok": True,
        "query": query,
        "contexto": contexto,
        "fuentes": fuentes,
        "total_fuentes": len(fuentes),
        "chars": len(contexto)
    }


def construir_prompt_rag(query, top_k=5):
    data = construir_contexto(query, top_k=top_k)

    if not data.get("ok"):
        return {
            "ok": False,
            "error": data.get("error")
        }

    prompt = f"""
Eres un asistente técnico del Agente IA.

Responde la pregunta usando SOLO el contexto recuperado.
Si el contexto no alcanza, dilo claramente.

PREGUNTA:
{query}

CONTEXTO RECUPERADO:
{data.get("contexto")}

INSTRUCCIONES:
- Responde claro y directo.
- Cita las fuentes internas por nombre de archivo y función si existen.
- No inventes información fuera del contexto.
"""

    return {
        "ok": True,
        "query": query,
        "prompt": prompt.strip(),
        "fuentes": data.get("fuentes", [])
    }


if __name__ == "__main__":
    query = input("Pregunta para construir contexto: ").strip()

    salida = construir_prompt_rag(query)

    print(json.dumps(salida, indent=2, ensure_ascii=False))
