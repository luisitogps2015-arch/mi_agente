import os
import json

CHUNKS_DIR = "data/chunks"


def buscar(query):

    resultados = []

    for archivo in os.listdir(CHUNKS_DIR):

        if not archivo.endswith(".json"):
            continue

        ruta = os.path.join(
            CHUNKS_DIR,
            archivo
        )

        try:

            with open(
                ruta,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except Exception:
            continue

        # ==========================
        # FORMATO NUEVO
        # [
        #   {chunk_id, content}
        # ]
        # ==========================

        if isinstance(data, list):

            chunks = data

        # ==========================
        # FORMATO VIEJO
        # {
        #   "chunks": [...]
        # }
        # ==========================

        elif isinstance(data, dict):

            chunks = data.get(
                "chunks",
                []
            )

        else:

            continue

        for chunk in chunks:

            if not isinstance(
                chunk,
                dict
            ):
                continue

            contenido = chunk.get(
                "content",
                ""
            )

            if query.lower() in contenido.lower():

                resultados.append({
                    "archivo": archivo,
                    "chunk_id": chunk.get(
                        "chunk_id",
                        "N/A"
                    ),
                    "contenido": contenido[:300]
                })

    return resultados


if __name__ == "__main__":

    query = input("Buscar: ")

    resultado = buscar(query)

    print(
        json.dumps(
            resultado,
            indent=2,
            ensure_ascii=False
        )
    )
