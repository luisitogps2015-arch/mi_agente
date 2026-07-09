import os
import json
import math
import re
from collections import Counter, defaultdict

from config import CHUNKS_DIR


def tokenize(texto):
    texto = texto.lower()
    return re.findall(r"\b\w+\b", texto)


def cargar_chunks():
    chunks = []

    if not os.path.exists(CHUNKS_DIR):
        return chunks

    for archivo in os.listdir(CHUNKS_DIR):
        if not archivo.endswith(".chunks.json"):
            continue

        ruta = os.path.join(CHUNKS_DIR, archivo)

        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)

        for chunk in data.get("chunks", []):
            chunks.append(chunk)

    return chunks


def calcular_bm25(query, chunks, k1=1.5, b=0.75):
    query_tokens = tokenize(query)
    documentos = [tokenize(c.get("content", "")) for c in chunks]

    total_docs = len(documentos)
    if total_docs == 0:
        return []

    avgdl = sum(len(doc) for doc in documentos) / total_docs

    df = {}
    for doc in documentos:
        for token in set(doc):
            df[token] = df.get(token, 0) + 1

    resultados = []

    for chunk, doc_tokens in zip(chunks, documentos):
        score = 0.0
        freqs = Counter(doc_tokens)
        doc_len = len(doc_tokens)

        for token in query_tokens:
            if token not in freqs:
                continue

            n_q = df.get(token, 0)
            idf = math.log(1 + ((total_docs - n_q + 0.5) / (n_q + 0.5)))
            tf = freqs[token]
            denom = tf + k1 * (1 - b + b * (doc_len / avgdl))
            score += idf * ((tf * (k1 + 1)) / denom)

        if score > 0:
            resultados.append({
                "metodo": "bm25",
                "score": round(score, 4),
                "chunk_id": chunk.get("chunk_id"),
                "source": chunk.get("source"),
                "tipo": chunk.get("tipo"),
                "nombre": chunk.get("nombre"),
                "index": chunk.get("index"),
                "content": chunk.get("content", "")[:1200]
            })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados


def construir_idf(documentos):
    total_docs = len(documentos)
    df = defaultdict(int)

    for doc in documentos:
        for token in set(doc):
            df[token] += 1

    return {
        token: math.log((total_docs + 1) / (freq + 1)) + 1
        for token, freq in df.items()
    }


def vector_tfidf(tokens, idf):
    freqs = Counter(tokens)
    total = max(len(tokens), 1)
    return {
        token: (freq / total) * idf.get(token, 0.0)
        for token, freq in freqs.items()
    }


def cosine_similarity(vec_a, vec_b):
    comunes = set(vec_a.keys()).intersection(vec_b.keys())
    numerador = sum(vec_a[t] * vec_b[t] for t in comunes)

    norma_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norma_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return numerador / (norma_a * norma_b)


def calcular_vector_tfidf(query, chunks):
    query_tokens = tokenize(query)
    documentos = [tokenize(c.get("content", "")) for c in chunks]

    if not documentos:
        return []

    idf = construir_idf(documentos)
    query_vector = vector_tfidf(query_tokens, idf)

    resultados = []

    for chunk, doc_tokens in zip(chunks, documentos):
        doc_vector = vector_tfidf(doc_tokens, idf)
        score = cosine_similarity(query_vector, doc_vector)

        if score > 0:
            resultados.append({
                "metodo": "tfidf_vector",
                "score": round(score, 4),
                "chunk_id": chunk.get("chunk_id"),
                "source": chunk.get("source"),
                "tipo": chunk.get("tipo"),
                "nombre": chunk.get("nombre"),
                "index": chunk.get("index"),
                "content": chunk.get("content", "")[:1200]
            })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados


def normalizar_scores(resultados):
    if not resultados:
        return []

    max_score = max(r["score"] for r in resultados)
    if max_score == 0:
        return resultados

    salida = []

    for r in resultados:
        nuevo = dict(r)
        nuevo["score_norm"] = round(r["score"] / max_score, 4)
        salida.append(nuevo)

    return salida


def fusionar_resultados(bm25, vectorial, peso_bm25=0.6, peso_vector=0.4):
    bm25 = normalizar_scores(bm25)
    vectorial = normalizar_scores(vectorial)

    fusion = {}

    for r in bm25:
        cid = r["chunk_id"]
        fusion[cid] = dict(r)
        fusion[cid]["bm25_score"] = r.get("score_norm", 0)
        fusion[cid]["vector_score"] = 0
        fusion[cid]["hybrid_score"] = peso_bm25 * r.get("score_norm", 0)

    for r in vectorial:
        cid = r["chunk_id"]

        if cid not in fusion:
            fusion[cid] = dict(r)
            fusion[cid]["bm25_score"] = 0
            fusion[cid]["vector_score"] = r.get("score_norm", 0)
            fusion[cid]["hybrid_score"] = peso_vector * r.get("score_norm", 0)
        else:
            fusion[cid]["vector_score"] = r.get("score_norm", 0)
            fusion[cid]["hybrid_score"] += peso_vector * r.get("score_norm", 0)

    resultados = list(fusion.values())
    resultados.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return resultados


def bonus_por_fuente_y_tipo(query, resultado):
    query_lower = query.lower()
    source = str(resultado.get("source", "")).lower()
    tipo = str(resultado.get("tipo", "")).lower()
    nombre = str(resultado.get("nombre", "")).lower()

    bonus = 0.0
    penalizacion = 0.0

    # Si la pregunta menciona un archivo, priorizar ese archivo
    if "mcp_client" in query_lower and "mcp_client.py" in source:
        bonus += 0.8

    if "mcp_server" in query_lower and "mcp_server.py" in source:
        bonus += 0.8

    if "agent_loop" in query_lower and "agent_loop.py" in source:
        bonus += 0.8

    if "plugin_registry" in query_lower and "plugin_registry.py" in source:
        bonus += 0.8

    if "herramientas" in query_lower and "herramientas.py" in source:
        bonus += 0.8

    # Si se pregunta por código, priorizar funciones/clases
    palabras_codigo = [
        "funciona", "ejecuta", "plugin", "funcion",
        "función", "codigo", "código", "client",
        "server", "registry", "loop"
    ]

    if any(p in query_lower for p in palabras_codigo):
        if tipo in ("function", "class", "module_preamble"):
            bonus += 0.4

        if source.endswith(".py"):
            bonus += 0.3

        if source == "historial.json":
            penalizacion += 0.5

    # Bonus si el nombre del chunk aparece en la pregunta
    for token in tokenize(query):
        if token and token in nombre:
            bonus += 0.25

    return bonus - penalizacion


def rerank_hibrido(query, resultados):
    query_tokens = set(tokenize(query))
    reranked = []

    for r in resultados:
        content_tokens = set(tokenize(r.get("content", "")))
        overlap = len(query_tokens.intersection(content_tokens))

        bonus_nombre = 0.0
        nombre = str(r.get("nombre", "")).lower()

        for token in query_tokens:
            if token in nombre:
                bonus_nombre += 0.2

        bonus_fuente_tipo = bonus_por_fuente_y_tipo(query, r)

        final_score = (
            r.get("hybrid_score", 0)
            + (overlap * 0.05)
            + bonus_nombre
            + bonus_fuente_tipo
        )

        nuevo = dict(r)
        nuevo["overlap"] = overlap
        nuevo["bonus_nombre"] = round(bonus_nombre, 4)
        nuevo["bonus_fuente_tipo"] = round(bonus_fuente_tipo, 4)
        nuevo["rerank_score"] = round(final_score, 4)

        reranked.append(nuevo)

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked


def buscar_contexto_hibrido(query, top_k=5):
    chunks = cargar_chunks()

    if not chunks:
        return {
            "ok": False,
            "error": "No hay chunks disponibles."
        }

    bm25 = calcular_bm25(query, chunks)
    vectorial = calcular_vector_tfidf(query, chunks)
    fusionados = fusionar_resultados(bm25, vectorial)
    reranked = rerank_hibrido(query, fusionados)

    return {
        "ok": True,
        "query": query,
        "total_chunks": len(chunks),
        "total_resultados": len(reranked),
        "resultados": reranked[:top_k]
    }


def buscar_contexto(query, top_k=5):
    return buscar_contexto_hibrido(query, top_k)


if __name__ == "__main__":
    query = input("Consulta: ").strip()
    resultado = buscar_contexto_hibrido(query)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
