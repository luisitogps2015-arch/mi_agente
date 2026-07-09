import os
import json
toggle_folder = 'toggle'

# Crear carpeta toggle si no existe
if not os.path.exists(toggle_folder):
    os.makedirs(toggle_folder)

# Funcion para activar/desactivar skill
def toggle_skill(skill_name):
    toggle_file = os.path.join(toggle_folder, f'{skill_name}.active')
    if os.path.exists(toggle_file):
        os.remove(toggle_file)
    else:
        open(toggle_file, 'w').close()

# Obtener lista de skills
skills_folder = 'skills'
skills_files = [f for f in os.listdir(skills_folder) if f.endswith('.py')]

# Monitorizar estado de skills y crear estado.json
estado = {'skills': {}}
for skill in skills_files:
    skill_name = skill[:-3]
    toggle_file = os.path.join(toggle_folder, f'{skill_name}.active')
    estado['skills'][skill_name] = os.path.exists(toggle_file)

with open('estado.json', 'w') as f:
    json.dump(estado, f)