import os
def run(params):
    resultado = []
    # Buscamos de forma recursiva desde la raíz para ver dónde están tus archivos
    for root, dirs, files in os.walk('/'):
        for file in files:
            if file.endswith('.py') or file.endswith('.json'):
                resultado.append(os.path.join(root, file))
        if len(resultado) > 50: break # Evitamos saturar
    return str(resultado)