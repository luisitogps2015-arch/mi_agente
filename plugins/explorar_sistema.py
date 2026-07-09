import os
import json
def run(params):
    # Buscamos en el directorio actual y en los hijos
    estructura = {}
    for root, dirs, files in os.walk('/):
        if 'app' in root or root == '/):
            estructura[root] = files
            if len(estructura) > 20: break # Limite para no saturar
    return json.dumps(estructura)