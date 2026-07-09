import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA_DIR = os.path.join(BASE_DIR, "proyectos", "_entrada")


def run(params=None):
    os.makedirs(ENTRADA_DIR, exist_ok=True)

    documentos = []

    for archivo in sorted(os.listdir(ENTRADA_DIR)):
        ruta = os.path.join(ENTRADA_DIR, archivo)

        if os.path.isfile(ruta):
            documentos.append({
                "archivo": archivo,
                "ruta": ruta,
                "extension": os.path.splitext(archivo)[1].lower(),
                "size_bytes": os.path.getsize(ruta)
            })

    return {
        "ok": True,
        "total": len(documentos),
        "entrada_dir": ENTRADA_DIR,
        "documentos": documentos
    }
