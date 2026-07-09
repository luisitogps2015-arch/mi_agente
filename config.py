import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_project_root():

    # Si estamos ejecutando desde el proyecto real
    if os.path.exists(os.path.join(BASE_DIR, "app.py")):
        return BASE_DIR

    # Si estamos dentro de Docker
    if os.path.exists("/app"):
        return "/app"

    return BASE_DIR

PROJECT_ROOT = get_project_root()

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
PLUGINS_DIR = os.path.join(PROJECT_ROOT, "plugins")
SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
DB_PATH = os.path.join(PROJECT_ROOT, "agente_data.db")
