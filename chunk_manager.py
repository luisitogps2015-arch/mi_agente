import os
import ast
import json
import hashlib
from datetime import datetime, timezone

from config import PROJECT_ROOT, CHUNKS_DIR

EXTENSIONES_PERMITIDAS = [".py", ".json", ".md", ".txt", ".log"]


def asegurar_directorio():
    os.makedirs(CHUNKS_DIR, exist_ok=True)


def ahora_utc():
    return datetime.now(timezone.utc).isoformat()


def calcular_hash(texto):
    return hashlib.sha256(texto.encode("utf-8", errors="ignore")).hexdigest()


def leer_archivo(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def dividir_por_tamano(texto, chunk_size=1200, overlap=200):
    chunks = []

    if not texto:
        return chunks

    inicio = 0
    total = len(texto)

    while inicio < total:
        fin = min(inicio + chunk_size, total)
        contenido = texto[inicio:fin]

        chunks.append({
            "tipo": "size",
            "nombre": f"chunk_{len(chunks)}",
            "start": inicio,
            "end": fin,
            "content": contenido
        })

        if fin >= total:
            break

        inicio = max(0, fin - overlap)

    return chunks


def chunk_python_por_estructura(texto):
    """
    Fragmenta archivos .py por estructura:
    - imports/top-level inicial
    - clases
    - funciones
    - bloques sueltos si existen
    """
    lineas = texto.splitlines(keepends=True)
    chunks = []

    try:
        tree = ast.parse(texto)
    except SyntaxError:
        return dividir_por_tamano(texto)

    nodos = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, "lineno", None)
            end = getattr(node, "end_lineno", None)

            if start and end:
                tipo = "class" if isinstance(node, ast.ClassDef) else "function"
                nodos.append({
                    "tipo": tipo,
                    "nombre": node.name,
                    "start_line": start,
                    "end_line": end
                })

    nodos.sort(key=lambda x: x["start_line"])

    # Bloque inicial antes de la primera función/clase: imports, constantes, config.
    if nodos:
        primera = nodos[0]["start_line"]
        if primera > 1:
            contenido = "".join(lineas[0:primera - 1]).strip()
            if contenido:
                chunks.append({
                    "tipo": "module_preamble",
                    "nombre": "imports_config",
                    "start_line": 1,
                    "end_line": primera - 1,
                    "content": contenido
                })
    else:
        return dividir_por_tamano(texto)

    # Funciones y clases
    for nodo in nodos:
        contenido = "".join(
            lineas[nodo["start_line"] - 1:nodo["end_line"]]
        ).strip()

        if contenido:
            chunks.append({
                "tipo": nodo["tipo"],
                "nombre": nodo["nombre"],
                "start_line": nodo["start_line"],
                "end_line": nodo["end_line"],
                "content": contenido
            })

    return chunks


def chunk_markdown_por_headers(texto):
    """
    Fragmenta Markdown por encabezados #, ##, ###.
    """
    lineas = texto.splitlines(keepends=True)
    chunks = []
    actual = []
    titulo = "inicio"
    start_line = 1

    for idx, linea in enumerate(lineas, start=1):
        if linea.lstrip().startswith("#") and actual:
            contenido = "".join(actual).strip()
            if contenido:
                chunks.append({
                    "tipo": "markdown_section",
                    "nombre": titulo,
                    "start_line": start_line,
                    "end_line": idx - 1,
                    "content": contenido
                })

            actual = [linea]
            titulo = linea.strip().replace("#", "").strip() or f"section_{idx}"
            start_line = idx
        else:
            if not actual:
                start_line = idx
                if linea.lstrip().startswith("#"):
                    titulo = linea.strip().replace("#", "").strip() or f"section_{idx}"
            actual.append(linea)

    if actual:
        contenido = "".join(actual).strip()
        if contenido:
            chunks.append({
                "tipo": "markdown_section",
                "nombre": titulo,
                "start_line": start_line,
                "end_line": len(lineas),
                "content": contenido
            })

    return chunks if chunks else dividir_por_tamano(texto)


def generar_partes_por_extension(ruta_absoluta, texto, chunk_size=1200, overlap=200):
    _, extension = os.path.splitext(ruta_absoluta)
    extension = extension.lower()

    if extension == ".py":
        return chunk_python_por_estructura(texto)

    if extension == ".md":
        return chunk_markdown_por_headers(texto)

    return dividir_por_tamano(texto, chunk_size, overlap)


def generar_chunks_archivo(ruta_relativa, chunk_size=1200, overlap=200):
    asegurar_directorio()

    ruta_absoluta = os.path.join(PROJECT_ROOT, ruta_relativa)

    if not os.path.exists(ruta_absoluta):
        return {
            "ok": False,
            "error": f"Archivo no encontrado: {ruta_absoluta}"
        }

    _, extension = os.path.splitext(ruta_absoluta)
    extension = extension.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        return {
            "ok": False,
            "error": f"Extension no permitida: {extension}"
        }

    texto = leer_archivo(ruta_absoluta)
    partes = generar_partes_por_extension(
        ruta_absoluta,
        texto,
        chunk_size,
        overlap
    )

    file_id = calcular_hash(ruta_relativa + texto)[:12]

    chunks_finales = []

    for index, parte in enumerate(partes):
        chunk_id = f"{file_id}_{index}"

        chunks_finales.append({
            "chunk_id": chunk_id,
            "source": ruta_relativa,
            "source_path": ruta_absoluta,
            "index": index,
            "tipo": parte.get("tipo", "unknown"),
            "nombre": parte.get("nombre", f"chunk_{index}"),
            "start": parte.get("start"),
            "end": parte.get("end"),
            "start_line": parte.get("start_line"),
            "end_line": parte.get("end_line"),
            "content": parte.get("content", ""),
            "content_hash": calcular_hash(parte.get("content", "")),
            "created_at": ahora_utc()
        })

    salida = {
        "ok": True,
        "source": ruta_relativa,
        "chunking_strategy": (
            "python_ast" if extension == ".py"
            else "markdown_headers" if extension == ".md"
            else "fixed_size_overlap"
        ),
        "total_chunks": len(chunks_finales),
        "chunks": chunks_finales
    }

    nombre_salida = (
        f"{file_id}_"
        f"{os.path.basename(ruta_relativa)}"
        f".chunks.json"
    )

    ruta_salida = os.path.join(CHUNKS_DIR, nombre_salida)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=2, ensure_ascii=False)

    return {
        "ok": True,
        "source": ruta_relativa,
        "strategy": salida["chunking_strategy"],
        "total_chunks": len(chunks_finales),
        "output": ruta_salida
    }


def listar_chunks():
    asegurar_directorio()

    archivos = [
        f for f in os.listdir(CHUNKS_DIR)
        if f.endswith(".chunks.json")
    ]

    return {
        "ok": True,
        "chunks_dir": CHUNKS_DIR,
        "archivos": archivos,
        "total": len(archivos)
    }


if __name__ == "__main__":
    archivo = input("Archivo a chunkear: ").strip()

    if not archivo:
        print("Debes indicar un archivo. Ejemplo: app.py")
    else:
        resultado = generar_chunks_archivo(archivo)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
