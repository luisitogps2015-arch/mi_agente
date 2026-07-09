from plugin_registry import run_plugin


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    contenido = params.get("contenido", "").strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido de reunión."
        }

    resultados = {}

    try:

        resultados["acta"] = run_plugin(
            "generar_acta_pm",
            {
                "proyecto_id": proyecto_id,
                "titulo": "Acta generada automáticamente",
                "contenido": contenido
            }
        )

        resultados["compromisos"] = run_plugin(
            "generar_compromisos_pm",
            {
                "proyecto_id": proyecto_id,
                "contenido": contenido
            }
        )

        resultados["backlog"] = run_plugin(
            "generar_backlog_pm",
            {
                "proyecto_id": proyecto_id,
                "contenido": contenido
            }
        )

        resultados["riesgos"] = run_plugin(
            "generar_riesgos_pm",
            {
                "proyecto_id": proyecto_id,
                "contenido": contenido
            }
        )

        resultados["informe"] = run_plugin(
            "generar_informe_pm",
            {
                "proyecto_id": proyecto_id,
                "titulo": "Informe Ejecutivo Automático",
                "contenido": contenido
            }
        )

        resultados["memoria"] = run_plugin(
            "guardar_memoria_proyecto_pm",
            {
                "proyecto_id": proyecto_id,
                "tipo": "reunion",
                "contenido": contenido
            }
        )

        resultados["contexto"] = run_plugin(
            "actualizar_contexto_proyecto_pm",
            {
                "proyecto_id": proyecto_id
            }
        )

        return {
            "ok": True,
            "mensaje": "Workflow PM ejecutado correctamente",
            "proyecto_id": proyecto_id,
            "resultados": resultados
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
