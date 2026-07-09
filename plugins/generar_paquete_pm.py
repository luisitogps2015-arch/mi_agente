import os
from datetime import datetime

from plugins.generar_acta_pm import run as generar_acta
from plugins.generar_compromisos_pm import run as generar_compromisos
from plugins.generar_backlog_pm import run as generar_backlog
from plugins.generar_riesgos_pm import run as generar_riesgos
from plugins.generar_informe_pm import run as generar_informe
from plugins.actualizar_contexto_proyecto_pm import run as actualizar_contexto

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    contenido = params.get("contenido", "").strip()
    titulo = params.get("titulo", "Paquete PM generado por PM Copilot")

    if not contenido:
        return {
            "ok": False,
            "error": "No se recibió contenido para generar el paquete PM."
        }

    resultados = {}

    resultados["acta"] = generar_acta({
        "proyecto_id": proyecto_id,
        "titulo": titulo,
        "contenido": contenido
    })

    resultados["compromisos"] = generar_compromisos({
        "proyecto_id": proyecto_id,
        "contenido": contenido
    })

    resultados["backlog"] = generar_backlog({
        "proyecto_id": proyecto_id,
        "contenido": contenido
    })

    resultados["riesgos"] = generar_riesgos({
        "proyecto_id": proyecto_id,
        "contenido": contenido
    })

    resultados["informe"] = generar_informe({
        "proyecto_id": proyecto_id,
        "titulo": "Informe Ejecutivo del Paquete PM",
        "contenido": contenido
    })

    resultados["contexto"] = actualizar_contexto({
        "proyecto_id": proyecto_id
    })

    errores = []

    for nombre, resultado in resultados.items():
        if not resultado.get("ok"):
            errores.append({
                "artefacto": nombre,
                "error": resultado.get("error", "Error no especificado")
            })

    return {
        "ok": len(errores) == 0,
        "mensaje": "Paquete PM generado correctamente" if not errores else "Paquete PM generado con errores parciales",
        "proyecto_id": proyecto_id,
        "fecha": datetime.utcnow().isoformat() + "Z",
        "artefactos_generados": resultados,
        "errores": errores
    }
