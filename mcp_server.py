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
    return {"ok": True, "acciones": list_plugins()}


def extraer_texto_despues(texto: str, prefijo: str) -> str:
    return texto[len(prefijo):].strip()


def ejecutar_desde_texto(texto: str) -> dict:
    texto_lower = texto.lower().strip()

    # ==========================
    # PM Copilot - Crear/Listar Proyectos
    # ==========================
    if texto_lower.startswith("crear proyecto "):
        nombre = extraer_texto_despues(texto, "crear proyecto ")
        return ejecutar_accion("crear_proyecto_pm", {
            "nombre": nombre,
            "descripcion": "Proyecto creado desde Telegram/Dashboard mediante PM Copilot"
        })

    if texto_lower in ["listar proyectos", "ver proyectos", "proyectos"]:
        return ejecutar_accion("listar_proyectos_pm", {})

    # ==========================
    # PM Copilot - Project Memory
    # ==========================
    if texto_lower.startswith("guardar memoria "):
        contenido = extraer_texto_despues(texto, "guardar memoria ")
        return ejecutar_accion("guardar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "nota",
            "contenido": contenido
        })

    if texto_lower.startswith("registrar acuerdo "):
        contenido = extraer_texto_despues(texto, "registrar acuerdo ")
        return ejecutar_accion("guardar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "acuerdo",
            "contenido": contenido
        })

    if texto_lower.startswith("registrar decision ") or texto_lower.startswith("registrar decisión "):
        prefijo = "registrar decisión " if texto_lower.startswith("registrar decisión ") else "registrar decision "
        contenido = extraer_texto_despues(texto, prefijo)
        return ejecutar_accion("guardar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "decision",
            "contenido": contenido
        })

    if texto_lower.startswith("registrar compromiso "):
        contenido = extraer_texto_despues(texto, "registrar compromiso ")
        return ejecutar_accion("guardar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "compromiso",
            "contenido": contenido
        })

    if texto_lower in ["consultar memoria proyecto", "ver memoria proyecto", "memoria proyecto"]:
        return ejecutar_accion("consultar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001"
        })

    if texto_lower == "ver acuerdos proyecto":
        return ejecutar_accion("consultar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "acuerdo"
        })

    if texto_lower == "ver decisiones proyecto":
        return ejecutar_accion("consultar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "decision"
        })

    if texto_lower == "ver compromisos proyecto":
        return ejecutar_accion("consultar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001",
            "tipo": "compromiso"
        })

    # ==========================
    # PM Copilot - Contexto Proyecto
    # ==========================
    if texto_lower in [
        "actualizar contexto proyecto",
        "construir contexto proyecto",
        "generar contexto proyecto"
    ]:
        return ejecutar_accion("actualizar_contexto_proyecto_pm", {
            "proyecto_id": "proyecto_001"
        })

    if texto_lower in [
        "consultar contexto proyecto",
        "ver contexto proyecto",
        "contexto proyecto"
    ]:
        return ejecutar_accion("consultar_memoria_proyecto_pm", {
            "proyecto_id": "proyecto_001"
        })

    if texto_lower in [
        "ingestar contexto proyecto",
        "ingestar contexto general proyecto"
    ]:
        return ejecutar_accion("ingestar_documento", {
            "ruta": "proyectos/proyecto_001/memoria/contexto_general.md"
        })

    # ==========================
    # PM Copilot - Artefactos
    # ==========================
    if texto_lower.startswith("generar paquete pm "):
        contenido = extraer_texto_despues(texto, "generar paquete pm ")

        return ejecutar_accion("generar_paquete_pm", {
            "proyecto_id": "proyecto_001",
            "titulo": "Paquete PM generado por PM Copilot",
            "contenido": contenido
        })

    if texto_lower.startswith("generar acta "):
        contenido = extraer_texto_despues(texto, "generar acta ")
        return ejecutar_accion("generar_acta_pm", {
            "proyecto_id": "proyecto_001",
            "titulo": "Acta generada por PM Copilot",
            "contenido": contenido
        })

    if texto_lower.startswith("generar minuta "):
        contenido = extraer_texto_despues(texto, "generar minuta ")
        return ejecutar_accion("generar_minuta_pm", {
            "proyecto_id": "proyecto_001",
            "titulo": "Minuta generada por PM Copilot",
            "contenido": contenido
        })

    if texto_lower.startswith("generar compromisos "):
        contenido = extraer_texto_despues(texto, "generar compromisos ")
        return ejecutar_accion("generar_compromisos_pm", {
            "proyecto_id": "proyecto_001",
            "contenido": contenido
        })

    if texto_lower.startswith("generar backlog "):
        contenido = extraer_texto_despues(texto, "generar backlog ")
        return ejecutar_accion("generar_backlog_pm", {
            "proyecto_id": "proyecto_001",
            "contenido": contenido
        })

    if texto_lower.startswith("generar informe ejecutivo "):
        contenido = extraer_texto_despues(texto, "generar informe ejecutivo ")
        return ejecutar_accion("generar_informe_pm", {
            "proyecto_id": "proyecto_001",
            "titulo": "Informe ejecutivo generado por PM Copilot",
            "contenido": contenido
        })

    if texto_lower.startswith("generar informe "):
        contenido = extraer_texto_despues(texto, "generar informe ")
        return ejecutar_accion("generar_informe_pm", {
            "proyecto_id": "proyecto_001",
            "titulo": "Informe ejecutivo generado por PM Copilot",
            "contenido": contenido
        })

    if texto_lower.startswith("generar riesgos "):
        contenido = extraer_texto_despues(texto, "generar riesgos ")
        return ejecutar_accion("generar_riesgos_pm", {
            "proyecto_id": "proyecto_001",
            "contenido": contenido
        })

    # ==========================
    # PM Copilot - Document Intake
    # ==========================
    if (
        texto_lower == "listar documentos"
        or texto_lower == "ver documentos"
        or texto_lower == "documentos entrada"
    ):
        return ejecutar_accion("listar_documentos_pm", {})

    if texto_lower.startswith("procesar documento "):
        ruta = extraer_texto_despues(texto, "procesar documento ")

        return ejecutar_accion("procesar_documento_pm", {
            "proyecto_id": "proyecto_001",
            "ruta": ruta,
            "titulo": "Documento procesado por PM Copilot"
        })

    # ==========================
    # PM Copilot - LangGraph
    # ==========================
    if texto_lower.startswith("grafo pm "):
        ruta = extraer_texto_despues(texto, "grafo pm ")

        return ejecutar_accion("grafo_pm", {
            "proyecto_id": "proyecto_001",
            "ruta": ruta
        })

    # ==========================
    # Core Agent
    # ==========================
    if texto_lower.startswith("autocurar "):
        objetivo = extraer_texto_despues(texto, "autocurar ")
        return ejecutar_accion("autocurar", {"objetivo": objetivo})

    if texto_lower.startswith("descomponer "):
        objetivo = extraer_texto_despues(texto, "descomponer ")
        return ejecutar_accion("descomponer", {"objetivo": objetivo})

    if texto_lower.startswith("planificar "):
        objetivo = extraer_texto_despues(texto, "planificar ")
        return ejecutar_accion("planificar", {"objetivo": objetivo})

    if texto_lower.startswith("razonar "):
        query = extraer_texto_despues(texto, "razonar ")
        return ejecutar_accion("razonar", {"query": query})

    if texto_lower.startswith("rag "):
        query = extraer_texto_despues(texto, "rag ")
        return ejecutar_accion("rag_responder", {"query": query})

    if texto_lower.startswith("buscar contexto "):
        query = extraer_texto_despues(texto, "buscar contexto ")
        return ejecutar_accion("buscar_contexto", {"query": query})

    if texto_lower.startswith("ingestar documento "):
        ruta = extraer_texto_despues(texto, "ingestar documento ")
        return ejecutar_accion("ingestar_documento", {"ruta": ruta})

    if texto_lower == "memoria":
        return ejecutar_accion("memoria", {"modo": "resumen"})

    if texto_lower == "memoria eventos":
        return ejecutar_accion("memoria", {"modo": "eventos"})

    if texto_lower == "chunks" or "listar chunks" in texto_lower or "ver chunks" in texto_lower:
        return ejecutar_accion("listar_chunks", {})

    if texto_lower == "logs" or "leer logs" in texto_lower or "ver logs" in texto_lower:
        return ejecutar_accion("leer_logs", {})

    if "alerta" in texto_lower or "telegram" in texto_lower:
        return ejecutar_accion("enviar_alerta", {"mensaje": texto})

    if "config" in texto_lower:
        return ejecutar_accion("leer_archivo_definitivo", {"nombre": "config.json"})

    if "mapa" in texto_lower or "sistema" in texto_lower:
        return ejecutar_accion("mapa_total", {})

    if "listar" in texto_lower or "archivos" in texto_lower:
        return ejecutar_accion("listar_contenido_real", {})

    if "archivo" in texto_lower:
        return ejecutar_accion("leer_archivo_definitivo", {"nombre": "config.json"})

    return {
        "ok": False,
        "plugin": "",
        "params": {},
        "resultado": "",
        "error": "No se encontró una acción adecuada para el texto recibido.",
        "texto": texto
    }


def procesar_agente(texto: str, chat_id=None) -> str:
    resultado = ejecutar_desde_texto(texto)

    if resultado.get("ok"):
        respuesta = resultado.get("resultado", "")

        if isinstance(respuesta, (dict, list)):
            return json.dumps(respuesta, indent=2, ensure_ascii=False)

        return str(respuesta)

    return json.dumps(resultado, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    entrada = input("Acción para ejecutar: ")
    salida = ejecutar_desde_texto(entrada)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
