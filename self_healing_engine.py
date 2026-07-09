import json
import os
import subprocess

from reflection_engine import generar_reflexion


PLUGIN_LOGS = "plugins/leer_logs.py"


def escribir_plugin_leer_logs():
    contenido = '''"""
Plugin autocurado para leer logs del sistema.
Lee archivos .log comunes del proyecto y devuelve las últimas líneas.
"""

import os


LOGS_PERMITIDOS = [
    "app.log",
    "bot.log",
    "cron.log",
    "noticias.log",
    "output.log"
]


def run(params):
    archivo = params.get("archivo", "app.log")
    lineas = int(params.get("lineas", 30))

    if archivo not in LOGS_PERMITIDOS:
        return f"Error: log no permitido. Opciones: {LOGS_PERMITIDOS}"

    if not os.path.exists(archivo):
        return f"Error: el archivo {archivo} no existe."

    try:
        with open(archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.readlines()

        ultimas = contenido[-lineas:]

        if not ultimas:
            return f"El archivo {archivo} está vacío."

        return "".join(ultimas)

    except Exception as e:
        return f"Error leyendo log {archivo}: {e}"
'''

    with open(PLUGIN_LOGS, "w", encoding="utf-8") as f:
        f.write(contenido)

    return True, f"Plugin autocurado actualizado: {PLUGIN_LOGS}"


def ejecutar_comando(comando):
    try:
        result = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20
        )

        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def autocurar(objetivo: str) -> dict:
    reflexion = generar_reflexion(objetivo)

    if not reflexion.get("ok"):
        return {
            "ok": False,
            "error": reflexion.get("error", "No se pudo generar reflexión."),
            "objetivo": objetivo
        }

    texto_reflexion = reflexion.get("reflexion", "").lower()

    if "leer logs" not in objetivo.lower() and "leer_logs" not in texto_reflexion:
        return {
            "ok": False,
            "objetivo": objetivo,
            "mensaje": "Self-Healing V1 solo soporta autocuración del plugin leer_logs.",
            "reflexion": reflexion.get("reflexion", "")
        }

    pasos = []

    ok, msg = escribir_plugin_leer_logs()
    pasos.append({
        "paso": 1,
        "accion": "actualizar_plugin",
        "estado": "COMPLETADO" if ok else "FALLIDO",
        "resultado": msg
    })

    validar = ejecutar_comando("python3 -m py_compile plugins/leer_logs.py")
    pasos.append({
        "paso": 2,
        "accion": "validar_sintaxis",
        "estado": "COMPLETADO" if validar.get("ok") else "FALLIDO",
        "resultado": validar
    })

    probar = ejecutar_comando(
        "python3 -c \"from plugin_registry import run_plugin; print(run_plugin('leer_logs', {'archivo':'app.log','lineas':5}))\""
    )
    pasos.append({
        "paso": 3,
        "accion": "probar_plugin",
        "estado": "COMPLETADO" if probar.get("ok") else "FALLIDO",
        "resultado": probar
    })

    estado_final = "COMPLETADO"

    if any(p.get("estado") == "FALLIDO" for p in pasos):
        estado_final = "FALLIDO"

    return {
        "ok": estado_final == "COMPLETADO",
        "version": "SELF_HEALING_V1",
        "objetivo": objetivo,
        "estado_final": estado_final,
        "pasos": pasos,
        "reflexion_base": reflexion.get("reflexion", "")
    }


if __name__ == "__main__":
    objetivo = input("Objetivo para autocurar: ").strip()
    salida = autocurar(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
