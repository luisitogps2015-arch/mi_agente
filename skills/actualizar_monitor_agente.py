import os
import json
import time

while True:
    # Escanear carpeta skills/
    skills_folder = os.path.join(os.path.expanduser('~'), 'mi-agente', 'skills')
    skills_files = [f for f in os.listdir(skills_folder) if f.endswith('.py')]
    
    # Obtener memoria y CPU
    # ... (código existente para obtener memoria y CPU)
    
    # Crear estado.json
    estado = {
        'memoria': memoria,
        'cpu': cpu,
        'skills': skills_files
    }
    with open('estado.json', 'w') as f:
        json.dump(estado, f)
    
    time.sleep(5)