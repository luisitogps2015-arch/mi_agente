import os
from herramientas import PROJECT_ROOT

def run(params):
    try:
        nombre = params.get("nombre")

        if not nombre:
            return "Error: falta parámetro nombre"

        ruta = os.path.join(PROJECT_ROOT, nombre)

        if not os.path.exists(ruta):
            return f"Error: {ruta} no existe"

        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return f"Error: {e}"
