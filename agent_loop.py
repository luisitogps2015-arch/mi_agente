"""
agent_loop.py — Primer cerebro del agente.
Recibe un objetivo, decide una acción, ejecuta mediante mcp_client.py
y evalúa si el resultado sirve.
"""

import json
from mcp_client import ejecutar_desde_texto, ejecutar_accion


def evaluar_resultado(respuesta: dict) -> dict:
    if not respuesta.get("ok"):
        return {
            "estado": "FAIL",
            "motivo": respuesta.get("error", "Error desconocido")
        }

    resultado = str(respuesta.get("resultado", "")).strip()

    if not resultado:
        return {
            "estado": "FAIL",
            "motivo": "Resultado vacío"
        }

    if "Error" in resultado or "no existe" in resultado or "Archivo no encontrado" in resultado:
        return {
            "estado": "WARNING",
            "motivo": resultado[:300]
        }

    return {
        "estado": "PASS",
        "motivo": "Resultado válido"
    }


def ejecutar_loop(objetivo: str, max_intentos: int = 3) -> dict:
    pasos = []

    for intento in range(1, max_intentos + 1):
        accion = ejecutar_desde_texto(objetivo)
        evaluacion = evaluar_resultado(accion)

        pasos.append({
            "intento": intento,
            "accion": accion,
            "evaluacion": evaluacion
        })

        if evaluacion["estado"] == "PASS":
            return {
                "ok": True,
                "objetivo": objetivo,
                "estado_final": "COMPLETADO",
                "pasos": pasos,
                "respuesta_final": accion.get("resultado")
            }

        # Reintento simple
        if "archivo" in objetivo.lower() or "config" in objetivo.lower():
            accion = ejecutar_accion("listar_contenido_real", {})
            evaluacion = evaluar_resultado(accion)
            pasos.append({
                "intento": intento,
                "accion": accion,
                "evaluacion": evaluacion,
                "nota": "Reintento usando listado de archivos"
            })

            if evaluacion["estado"] == "PASS":
                return {
                    "ok": True,
                    "objetivo": objetivo,
                    "estado_final": "COMPLETADO_CON_REINTENTO",
                    "pasos": pasos,
                    "respuesta_final": accion.get("resultado")
                }

    return {
        "ok": False,
        "objetivo": objetivo,
        "estado_final": "NO_COMPLETADO",
        "pasos": pasos,
        "respuesta_final": "No se pudo completar el objetivo."
    }


if __name__ == "__main__":
    objetivo = input("Objetivo del agente: ")
    salida = ejecutar_loop(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
