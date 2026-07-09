"""
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
