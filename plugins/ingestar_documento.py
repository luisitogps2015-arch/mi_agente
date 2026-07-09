from document_ingestion import ingestar_documento


def run(params):

    ruta = params.get("ruta", "")

    if not ruta:
        return {
            "ok": False,
            "error": "Debes enviar la ruta del documento."
        }

    resultado = ingestar_documento(ruta)

    if not resultado.get("ok"):
        return {
            "ok": False,
            "error": resultado.get("error", "Error al ingestar documento")
        }

    return {
        "ok": True,
        "name": "ingestar_documento",
        "type": "plugin",
        "result": resultado
    }
