import os
import json
from datetime import datetime

from chunk_manager import generar_chunks_archivo


METADATA_DIR = "data/metadata"


def ingestar_documento(ruta_archivo):

    if not os.path.exists(ruta_archivo):
        return {
            "ok": False,
            "error": "Archivo no encontrado",
            "ruta": ruta_archivo
        }

    nombre = os.path.basename(ruta_archivo)

    resultado_chunks = generar_chunks_archivo(ruta_archivo)

    if not resultado_chunks.get("ok"):
        return {
            "ok": False,
            "error": resultado_chunks.get("error"),
            "documento": nombre
        }

    metadata = {
        "nombre": nombre,
        "ruta": ruta_archivo,
        "fecha_ingesta": datetime.now().isoformat(),
        "estado": "INGESTADO",
        "chunking_strategy": resultado_chunks.get("strategy"),
        "total_chunks": resultado_chunks.get("total_chunks"),
        "chunks_file": resultado_chunks.get("output")
    }

    metadata_file = os.path.join(
        METADATA_DIR,
        f"{nombre}.metadata.json"
    )

    with open(
        metadata_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

    return {
        "ok": True,
        "documento": nombre,
        "metadata": metadata_file,
        "chunking_strategy": resultado_chunks.get("strategy"),
        "total_chunks": resultado_chunks.get("total_chunks"),
        "chunks_file": resultado_chunks.get("output")
    }


if __name__ == "__main__":

    ruta = input("Documento: ").strip()

    resultado = ingestar_documento(ruta)

    print(
        json.dumps(
            resultado,
            indent=2,
            ensure_ascii=False
        )
    )
