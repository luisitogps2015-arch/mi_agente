import json
import os
import sqlite3
import subprocess
import sys
import requests
from ddgs import DDGS

# ── Configuración de rutas ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_project_root():
    """
    Detecta la raíz real del proyecto.
    En Docker normalmente será /app.
    En el host normalmente será /home/ubuntu/mi-agente.
    """
    rutas = [
        "/app",
        "/home/ubuntu/mi-agente",
        BASE_DIR,
    ]

    for ruta in rutas:
        if os.path.exists(ruta):
            return ruta

    return BASE_DIR

PROJECT_ROOT = get_project_root()
DB_PATH       = os.path.join(PROJECT_ROOT, "agente_data.db")
PLUGINS_DIR   = os.path.join(PROJECT_ROOT, "plugins")
SKILLS_DIR    = os.path.join(PROJECT_ROOT, "skills")
DATA_DIR      = os.path.join(PROJECT_ROOT, "data")

# ── Variables de entorno ──────────────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY",   "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY",  "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN",  "")
CHAT_ID        = os.getenv("CHAT_ID",         "")

MODELO = "openai/gpt-oss-20b"


# ── SQLite helpers ────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historial (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                role    TEXT,
                content TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS errores (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha     TEXT DEFAULT (datetime('now')),
                json_data TEXT
            )
        """)
        conn.commit()


def guardar_mensaje(chat_id, role, content):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO historial (chat_id, role, content) VALUES (?, ?, ?)",
            (str(chat_id), role, content)
        )
        conn.commit()


def cargar_historial(chat_id, limite=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM historial WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (str(chat_id), limite)
        ).fetchall()

    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def registrar_error(detalle):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO errores (json_data) VALUES (?)",
            (json.dumps(detalle, ensure_ascii=False),)
        )
        conn.commit()


# ── Búsqueda con DuckDuckGo ───────────────────────────────────────────────────
def buscar_duckduckgo(query):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=3))

        if not resultados:
            return "No se encontraron resultados."

        lineas = ["Resultados encontrados:"]

        for r in resultados:
            lineas.append(
                f"TITULO: {r['title']} | CONTENIDO: {r['body']} | LINK: {r['href']}"
            )

        return "\n".join(lineas)

    except Exception as e:
        return f"Error DuckDuckGo: {e}"


# ── Búsqueda con Tavily ───────────────────────────────────────────────────────
def buscar_tavily(query):
    if not TAVILY_API_KEY:
        return None

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 3
            },
            timeout=10,
        )

        if resp.status_code == 200:
            articulos = resp.json().get("results", [])

            if articulos:
                lineas = ["Resultados encontrados:"]

                for art in articulos:
                    lineas.append(
                        f"TITULO: {art['title']} | "
                        f"CONTENIDO: {art['content']} | "
                        f"LINK: {art.get('url', 'N/A')}"
                    )

                return "\n".join(lineas)

        return None

    except Exception:
        return None


# ── Búsqueda unificada ────────────────────────────────────────────────────────
def buscar_en_web_real(query):
    resultado = buscar_tavily(query)

    if resultado:
        return resultado

    print(f"[INFO] Tavily no disponible, usando DuckDuckGo para: {query}")
    return buscar_duckduckgo(query)


# ── Ejecutor de herramientas Groq ─────────────────────────────────────────────
def ejecutar_herramienta(metodo, args):
    if metodo == "buscar_internet":
        return buscar_en_web_real(args.get("query", ""))

    if metodo in ("crear_plugin", "autocura_plugin"):
        nombre = args.get("nombre", "")
        codigo = args.get("codigo", "")

        if not nombre or not codigo:
            return "Faltan parametros: nombre y codigo."

        os.makedirs(PLUGINS_DIR, exist_ok=True)

        with open(
            os.path.join(PLUGINS_DIR, f"{nombre}.py"),
            "w",
            encoding="utf-8"
        ) as f:
            f.write(codigo)

        return f"Plugin '{nombre}' guardado en {PLUGINS_DIR}."

    if metodo == "instalar_libreria":
        lib = args.get("nombre_libreria", "")

        if not lib:
            return "Falta parametro nombre_libreria."

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", lib, "--user"],
            capture_output=True,
            text=True
        )

        return f"Instalacion de '{lib}':\n{result.stdout or result.stderr}"

    return f"Herramienta '{metodo}' no reconocida."


# ── Tools para Groq ───────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_internet",
            "description": "Busca informacion real y reciente en internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_plugin",
            "description": "Crea un archivo .py en la carpeta de plugins.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "codigo": {"type": "string"}
                },
                "required": ["nombre", "codigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "autocura_plugin",
            "description": "Repara o actualiza un plugin existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "codigo": {"type": "string"}
                },
                "required": ["nombre", "codigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "instalar_libreria",
            "description": "Instala una libreria Python con pip.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_libreria": {"type": "string"}
                },
                "required": ["nombre_libreria"]
            }
        }
    },
]
