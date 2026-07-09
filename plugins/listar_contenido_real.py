import os
from herramientas import PROJECT_ROOT

def run(params):
    try:
        archivos = os.listdir(PROJECT_ROOT)
        return str(archivos)
    except Exception as e:
        return f"Error: {e}"
