from chunk_manager import listar_chunks

def run(params):
    resultado = listar_chunks()

    if not resultado.get("ok"):
        return f"Error: {resultado.get('error')}"

    archivos = resultado.get("archivos", [])

    if not archivos:
        return "No hay chunks creados todavía."

    return (
        f"Chunks encontrados: {resultado.get('total')}\n\n"
        + "\n".join(archivos)
    )
