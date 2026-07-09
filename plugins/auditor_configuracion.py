import json
import os

def run(params):
    # Archivos que queremos inspeccionar
    archivos_a_leer = ['config.json', 'tareas.json', 'historial.json', 'app.py']
    resultados = {}

    for nombre in archivos_a_leer:
        ruta = f'/app/{nombre}'
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r') as f:
                    resultados[nombre] = f.read()
            except Exception as e:
                resultados[nombre] = f"Error al leer: {str(e)}"
        else:
            resultados[nombre] = "Archivo no encontrado"

    return json.dumps(resultados)