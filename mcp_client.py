"""
mcp_client.py — Executor oficial del agente.

Responsabilidad:
- Recibir una acción.
- Validar el plugin.
- Ejecutar el plugin mediante plugin_registry.
- Devolver una respuesta estándar al agent_loop.py.
"""

import json
from plugin_registry import run_plugin, validate_plugin, list_plugins


def ejecutar_accion(nombre_plugin: str, params=None) -> dict:
    params = params or {}

    validacion = validate_plugin(nombre_plugin)

    if not validacion.get("ok"):
        return {
            "ok": False,
            "plugin": nombre_plugin,
            "params": params,
            "resultado": "",
            "error": validacion.get("error", "Plugin inválido")
        }

    resultado = run_plugin(nombre_plugin, params)

    return {
        "ok": resultado.get("ok", False),
        "plugin": nombre_plugin,
        "params": params,
        "resultado": resultado.get("result", ""),
        "error": resultado.get("error", "")
    }


def listar_acciones_disponibles() -> dict:
    return {
        "ok": True,
        "acciones": list_plugins()
    }


def ejecutar_desde_texto(texto: str) -> dict:
    texto_lower = texto.lower().strip()

    # ==========================
    # Document Ingestion
    # ==========================
    if texto_lower.startswith("ingestar documento "):
        ruta = texto[len("ingestar documento "):].strip()
        return ejecutar_accion(
            "ingestar_documento",
            {"ruta": ruta}
        )

    # ==========================
    # Self-Healing
    # ==========================
    if texto_lower.startswith("autocurar "):
        objetivo = texto[10:].strip()
        return ejecutar_accion("autocurar", {"objetivo": objetivo})

    # ==========================
    # Task Decomposer
    # ==========================
    if texto_lower.startswith("descomponer "):
        objetivo = texto[12:].strip()
        return ejecutar_accion("descomponer", {"objetivo": objetivo})

    # ==========================
    # Planner
    # ==========================
    if texto_lower.startswith("planificar "):
        objetivo = texto[11:].strip()
        return ejecutar_accion("planificar", {"objetivo": objetivo})

    # ==========================
    # Reasoning
    # ==========================
    if texto_lower.startswith("razonar "):
        query = texto[8:].strip()
        return ejecutar_accion("razonar", {"query": query})

    # ==========================
    # RAG
    # ==========================
    if texto_lower.startswith("rag "):
        query = texto[4:].strip()
        return ejecutar_accion("rag_responder", {"query": query})

    # ==========================
    # Context Builder
    # ==========================
    if texto_lower.startswith("buscar contexto "):
        query = texto[16:].strip()
        return ejecutar_accion("buscar_contexto", {"query": query})

    # ==========================
    # Goal Manager
    # ==========================
    if texto_lower == "objetivos":
        return ejecutar_accion("objetivos", {"modo": "listar"})

    if texto_lower == "objetivos pendientes":
        return ejecutar_accion("objetivos", {"modo": "pendientes"})

    if texto_lower.startswith("crear objetivo "):
        objetivo = texto[15:].strip()
        return ejecutar_accion(
            "objetivos",
            {
                "modo": "crear",
                "objetivo": objetivo
            }
        )

    if texto_lower.startswith("eliminar objetivo "):
        goal_id = texto[18:].strip()
        return ejecutar_accion(
            "objetivos",
            {
                "modo": "eliminar",
                "id": goal_id
            }
        )

    if texto_lower.startswith("ver objetivo "):
        goal_id = texto[13:].strip()
        return ejecutar_accion(
            "objetivos",
            {
                "modo": "ver",
                "id": goal_id
            }
        )

    # ==========================
    # Memory Manager
    # ==========================
    if texto_lower == "memoria":
        return ejecutar_accion("memoria", {"modo": "resumen"})

    if texto_lower == "memoria eventos":
        return ejecutar_accion("memoria", {"modo": "eventos"})

    # ==========================
    # Chunks
    # ==========================
    if (
        texto_lower == "chunks"
        or "listar chunks" in texto_lower
        or "ver chunks" in texto_lower
    ):
        return ejecutar_accion("listar_chunks", {})

    # ==========================
    # Logs
    # ==========================
    if (
        texto_lower == "logs"
        or "leer logs" in texto_lower
        or "ver logs" in texto_lower
    ):
        return ejecutar_accion("leer_logs", {})

    # ==========================
    # Telegram / Alertas
    # ==========================
    if "alerta" in texto_lower or "telegram" in texto_lower:
        return ejecutar_accion("enviar_alerta", {"mensaje": texto})

    # ==========================
    # Configuración
    # ==========================
    if "config" in texto_lower:
        return ejecutar_accion(
            "leer_archivo_definitivo",
            {"nombre": "config.json"}
        )

    # ==========================
    # Exploración del sistema
    # ==========================
    if "mapa" in texto_lower or "sistema" in texto_lower:
        return ejecutar_accion("mapa_total", {})

    # ==========================
    # Archivos
    # ==========================
    if "listar" in texto_lower or "archivos" in texto_lower:
        return ejecutar_accion("listar_contenido_real", {})

    if "archivo" in texto_lower:
        return ejecutar_accion(
            "leer_archivo_definitivo",
            {"nombre": "config.json"}
        )

    return {
        "ok": False,
        "plugin": "",
        "params": {},
        "resultado": "",
        "error": "No se encontró una acción adecuada para el texto recibido.",
        "texto": texto
    }


if __name__ == "__main__":
    entrada = input("Acción para ejecutar: ")
    salida = ejecutar_desde_texto(entrada)

    print(
        json.dumps(
            salida,
            indent=2,
            ensure_ascii=False
        )
    )
