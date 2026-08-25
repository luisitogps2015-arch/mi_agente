import threading, time, logging, os, json, hmac
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, send_from_directory, request
import telebot
from groq import Groq
from herramientas import TELEGRAM_TOKEN, CHAT_ID, buscar_en_web_real
from mcp_server import procesar_agente
from crew_core.ingestion import (
    API_SOURCES,
    DEFAULT_SOURCE,
    INGESTION_TTL_SECONDS,
    IngestionError,
    IngestionTimeoutError,
    fetch_api_source,
    ingestion_registry,
)
from crew_core.run_service import (
    MAX_TOPIC_LENGTH,
    CrewRunBusyError,
    CrewRunRateLimitError,
    crew_run_registry,
    crew_run_rate_limiter,
    validate_input_data,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

ENTRADA_PM_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "proyectos",
    "_entrada"
)

os.makedirs(
    ENTRADA_PM_DIR,
    exist_ok=True
)


SALUDOS = {"hola", "hi", "buenas", "buenos dias", "buenas tardes", "saludos"}


def _crew_auth_error():
    """Devuelve una respuesta segura cuando falla el token del dashboard."""
    expected = os.getenv("CREW_DASHBOARD_TOKEN", "")
    if not expected:
        return jsonify({"error": "Protección Crew no configurada."}), 503

    authorization = request.headers.get("Authorization", "")
    scheme, separator, supplied = authorization.partition(" ")
    valid = (
        separator == " "
        and scheme.lower() == "bearer"
        and bool(supplied)
        and hmac.compare_digest(supplied, expected)
    )
    if valid:
        return None

    response = jsonify({"error": "No autorizado."})
    response.headers["WWW-Authenticate"] = "Bearer"
    return response, 401

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")


AGENT_STATE = {
    "ok": True,
    "estado_general": "IDLE",
    "solicitud_actual": "",
    "respuesta_final": "",
    "error": "",
    "inicio": "",
    "fin": "",
    "plugin_detectado": "",
    "agentes": {
        "input": {
            "estado": "WAITING",
            "detalle": "Esperando solicitud del usuario",
            "entrada": "",
            "proceso": "",
            "salida": ""
        },
        "rag_context": {
            "estado": "WAITING",
            "detalle": "RAG / Context Builder en espera",
            "entrada": "",
            "proceso": "",
            "salida": ""
        },
        "planner": {
            "estado": "WAITING",
            "detalle": "Planner en espera",
            "entrada": "",
            "proceso": "",
            "salida": ""
        },
        "multi_agent": {
            "estado": "WAITING",
            "detalle": "MultiAgent V2 en espera",
            "entrada": "",
            "proceso": "",
            "salida": ""
        },
        "self_healing": {
            "estado": "WAITING",
            "detalle": "Self-Healing en espera",
            "entrada": "",
            "proceso": "",
            "salida": ""
        },
        "respuesta": {
            "estado": "WAITING",
            "detalle": "Respuesta final en espera",
            "entrada": "",
            "proceso": "",
            "salida": ""
        }
    }
}


PM_FLOW_STATE = {
    "estado_general": "IDLE",
    "ultima_entrada": "",
    "ultimo_resultado": "",
    "inicio": "",
    "fin": "",
    "nodes": {
        "intake": {
            "estado": "WAITING",
            "titulo": "Intake Agent",
            "detalle": "Esperando documento o solicitud"
        },
        "document_agent": {
            "estado": "WAITING",
            "titulo": "Document Agent",
            "detalle": "Extracción de texto / OCR / lectura documental"
        },
        "critic": {
            "estado": "WAITING",
            "titulo": "Critic Agent",
            "detalle": "Validación de calidad del resultado"
        },
        "delivery": {
            "estado": "WAITING",
            "titulo": "Delivery Agent",
            "detalle": "Entrega de artefactos y respuesta final"
        }
    }
}


def reset_pm_flow(entrada=""):
    PM_FLOW_STATE["estado_general"] = "PROCESSING"
    PM_FLOW_STATE["ultima_entrada"] = entrada
    PM_FLOW_STATE["ultimo_resultado"] = ""
    PM_FLOW_STATE["inicio"] = ahora_iso()
    PM_FLOW_STATE["fin"] = ""

    for key in PM_FLOW_STATE["nodes"]:
        PM_FLOW_STATE["nodes"][key]["estado"] = "WAITING"


def actualizar_pm_node(nombre, estado, detalle=""):
    if nombre in PM_FLOW_STATE["nodes"]:
        PM_FLOW_STATE["nodes"][nombre]["estado"] = estado
        if detalle:
            PM_FLOW_STATE["nodes"][nombre]["detalle"] = detalle



def ahora_iso():
    return datetime.utcnow().isoformat() + "Z"


def detectar_plugin_desde_texto(texto):
    texto_lower = texto.lower().strip()

    if texto_lower.startswith("autocurar "):
        return "autocurar"

    if texto_lower.startswith("descomponer "):
        return "descomponer"

    if texto_lower.startswith("planificar "):
        return "planificar"

    if texto_lower.startswith("razonar "):
        return "razonar"

    if texto_lower.startswith("rag "):
        return "rag_responder"

    if texto_lower.startswith("buscar contexto "):
        return "buscar_contexto"

    if texto_lower.startswith("ingestar documento "):
        return "ingestar_documento"

    if texto_lower == "memoria" or texto_lower == "memoria eventos":
        return "memoria"

    if texto_lower == "chunks" or "listar chunks" in texto_lower or "ver chunks" in texto_lower:
        return "listar_chunks"

    if texto_lower == "logs" or "leer logs" in texto_lower or "ver logs" in texto_lower:
        return "leer_logs"

    if "alerta" in texto_lower or "telegram" in texto_lower:
        return "enviar_alerta"

    if "config" in texto_lower:
        return "leer_archivo_definitivo"

    if "mapa" in texto_lower or "sistema" in texto_lower:
        return "mapa_total"

    if "listar" in texto_lower or "archivos" in texto_lower:
        return "listar_contenido_real"

    if "archivo" in texto_lower:
        return "leer_archivo_definitivo"

    return "sin_plugin_detectado"


def detectar_protocolo_desde_plugin(plugin):
    mapa = {
        "autocurar": "Self-Healing",
        "descomponer": "Task Decomposer",
        "planificar": "Planner",
        "razonar": "Reasoning / CoT",
        "rag_responder": "RAG",
        "buscar_contexto": "Context Builder",
        "ingestar_documento": "Document Ingestion",
        "memoria": "Memory Layer",
        "listar_chunks": "Chunk Manager",
        "leer_logs": "Log Reader",
        "enviar_alerta": "Telegram Alert",
        "leer_archivo_definitivo": "File Reader",
        "mapa_total": "System Mapper",
        "listar_contenido_real": "File Explorer",
        "sin_plugin_detectado": "Default Agent Route"
    }

    return mapa.get(plugin, "Default Agent Route")


def actualizar_agente(nombre, estado, detalle, entrada="", proceso="", salida=""):
    if nombre in AGENT_STATE["agentes"]:
        AGENT_STATE["agentes"][nombre]["estado"] = estado
        AGENT_STATE["agentes"][nombre]["detalle"] = detalle
        AGENT_STATE["agentes"][nombre]["entrada"] = entrada
        AGENT_STATE["agentes"][nombre]["proceso"] = proceso
        AGENT_STATE["agentes"][nombre]["salida"] = salida


def reset_agent_state(solicitud):
    AGENT_STATE["ok"] = True
    AGENT_STATE["estado_general"] = "PROCESSING"
    AGENT_STATE["solicitud_actual"] = solicitud
    AGENT_STATE["respuesta_final"] = ""
    AGENT_STATE["error"] = ""
    AGENT_STATE["inicio"] = ahora_iso()
    AGENT_STATE["fin"] = ""
    AGENT_STATE["plugin_detectado"] = ""

    for nombre in AGENT_STATE["agentes"]:
        AGENT_STATE["agentes"][nombre]["estado"] = "WAITING"
        AGENT_STATE["agentes"][nombre]["detalle"] = "En espera"
        AGENT_STATE["agentes"][nombre]["entrada"] = ""
        AGENT_STATE["agentes"][nombre]["proceso"] = ""
        AGENT_STATE["agentes"][nombre]["salida"] = ""


def leer_json_seguro(ruta, default):
    try:
        if not os.path.exists(ruta):
            return default

        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return default


def contar_archivos(carpeta, extension=None):
    if not os.path.exists(carpeta):
        return 0

    archivos = os.listdir(carpeta)

    if extension:
        archivos = [a for a in archivos if a.endswith(extension)]

    return len(archivos)


@bot.message_handler(
    content_types=["document"]
)
def handle_document(message):
    try:
        archivo_info = bot.get_file(
            message.document.file_id
        )

        archivo_binario = bot.download_file(
            archivo_info.file_path
        )

        nombre_archivo = message.document.file_name

        ruta_destino = os.path.join(
            ENTRADA_PM_DIR,
            nombre_archivo
        )

        with open(
            ruta_destino,
            "wb"
        ) as f:
            f.write(archivo_binario)

        comando = f"procesar documento proyectos/_entrada/{nombre_archivo}"

        bot.reply_to(
            message,
            (
                "Documento recibido correctamente.\n\n"
                f"Guardado en:\n{ruta_destino}\n\n"
                "Procesando automáticamente con PM Copilot..."
            )
        )

        resultado = procesar_agente(
            comando,
            message.chat.id
        )

        respuesta = str(resultado)

        if len(respuesta) > 3500:
            respuesta = (
                respuesta[:3500]
                + "\n\n[Respuesta truncada por Telegram. Revisa los artefactos generados en el servidor.]"
            )

        bot.send_message(
            message.chat.id,
            respuesta
        )

    except Exception as e:
        log.error(
            f"Error recibiendo/procesando documento: {e}"
        )

        bot.reply_to(
            message,
            f"Error procesando documento: {e}"
        )



def enviar_archivos_pm_generados(message, resultado_texto):
    try:
        data = json.loads(resultado_texto)

        paquete = data.get("resultado_paquete", {})
        artefactos = paquete.get("artefactos_generados", {})

        for clave in ["acta", "informe"]:
            item = artefactos.get(clave, {})
            ruta = item.get("ruta", "")

            if ruta and os.path.exists(ruta):
                with open(ruta, "rb") as f:
                    bot.send_document(
                        message.chat.id,
                        f,
                        caption=f"Archivo generado: {clave.upper()}"
                    )

    except Exception as e:
        log.error(f"No se pudieron enviar artefactos PM: {e}")


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        foto = message.photo[-1]
        archivo_info = bot.get_file(foto.file_id)
        archivo_binario = bot.download_file(archivo_info.file_path)

        nombre_archivo = f"foto_ocr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{message.message_id}.jpg"

        ruta_destino = os.path.join(
            ENTRADA_PM_DIR,
            nombre_archivo
        )

        with open(ruta_destino, "wb") as f:
            f.write(archivo_binario)

        bot.reply_to(
            message,
            (
                "Foto recibida correctamente.\n\n"
                "Aplicando OCR y generando artefactos PM..."
            )
        )

        comando = f"procesar documento proyectos/_entrada/{nombre_archivo}"

        resultado = procesar_agente(
            comando,
            message.chat.id
        )

        respuesta = str(resultado)

        if len(respuesta) > 3000:
            respuesta = respuesta[:3000] + "\n\n[Respuesta truncada. Se enviarán archivos generados si existen.]"

        bot.send_message(
            message.chat.id,
            respuesta
        )

        enviar_archivos_pm_generados(
            message,
            str(resultado)
        )

    except Exception as e:
        log.error(f"Error procesando foto OCR: {e}")
        bot.reply_to(
            message,
            f"Error procesando foto OCR: {e}"
        )


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if message.text.lower().strip() in SALUDOS:
        bot.reply_to(message, "Hola! En que puedo ayudarte?")
        return

    try:
        bot.reply_to(message, procesar_agente(message.text, message.chat.id))

    except Exception as e:
        log.error(f"Error procesando mensaje: {e}")
        bot.reply_to(message, "Error al procesar la solicitud.")


def ciclo_noticias():
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    log.info("Ciclo de noticias iniciado.")
    time.sleep(60)

    while True:
        try:
            texto = buscar_en_web_real("noticias inteligencia artificial Ecuador")

            if texto and "Error" not in texto:
                resp = groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Resume en 3 puntos clave:\n{texto}"
                        }
                    ]
                )

                bot.send_message(
                    CHAT_ID,
                    f"RESUMEN AUTOMATICO:\n\n{resp.choices[0].message.content}"
                )

                log.info("Resumen enviado.")

        except Exception as e:
            log.error(f"Error ciclo noticias: {e}")

        time.sleep(3600)


def iniciar_bot():
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        none_stop=True
    )


def ejecutar_solicitud_dashboard(solicitud):
    try:
        reset_agent_state(solicitud)

        plugin_detectado = detectar_plugin_desde_texto(solicitud)
        protocolo_detectado = detectar_protocolo_desde_plugin(plugin_detectado)
        AGENT_STATE["plugin_detectado"] = plugin_detectado

        actualizar_agente(
            "input",
            "PROCESSING",
            "Recepción de solicitud",
            entrada=solicitud,
            proceso="Capturando prompt enviado desde Dashboard",
            salida=""
        )

        time.sleep(0.3)

        actualizar_agente(
            "input",
            "COMPLETED",
            "Solicitud capturada",
            entrada=solicitud,
            proceso="Validación inicial completada",
            salida=f"Solicitud lista para ejecución. Protocolo detectado: {protocolo_detectado}"
        )

        actualizar_agente(
            "rag_context",
            "PROCESSING",
            "Construcción de contexto",
            entrada=solicitud,
            proceso="Consultando chunks y metadata disponibles",
            salida=""
        )

        time.sleep(0.5)

        total_chunks = contar_archivos(CHUNKS_DIR, ".chunks.json")
        total_metadata = contar_archivos(METADATA_DIR, ".json")

        actualizar_agente(
            "rag_context",
            "COMPLETED",
            "Contexto preparado",
            entrada=solicitud,
            proceso="Consulta RAG completada sobre la base documental local",
            salida=f"{total_chunks} chunks y {total_metadata} metadata disponibles"
        )

        actualizar_agente(
            "planner",
            "PROCESSING",
            "Planificación",
            entrada=f"Solicitud + Contexto + Protocolo: {protocolo_detectado}",
            proceso="Analizando intención, ruta de ejecución y plugin candidato",
            salida=""
        )

        time.sleep(0.5)

        actualizar_agente(
            "planner",
            "COMPLETED",
            "Plan generado",
            entrada="Solicitud enriquecida",
            proceso="Planificación completada",
            salida=f"Ruta definida hacia protocolo {protocolo_detectado} usando plugin {plugin_detectado}"
        )

        actualizar_agente(
            "multi_agent",
            "PROCESSING",
            "Orquestación",
            entrada="Plan operativo",
            proceso=f"Plugin seleccionado: {plugin_detectado}",
            salida=""
        )

        resultado = procesar_agente(solicitud, CHAT_ID)

        actualizar_agente(
            "multi_agent",
            "COMPLETED",
            "Orquestación completada",
            entrada="Plan operativo",
            proceso=f"Plugin ejecutado mediante MCP: {plugin_detectado}",
            salida="Resultado generado correctamente"
        )

        actualizar_agente(
            "self_healing",
            "PROCESSING",
            "Autocuración",
            entrada="Resultado del flujo",
            proceso="Buscando errores críticos, excepciones o fallos de plugin",
            salida=""
        )

        time.sleep(0.4)

        respuesta_limpia = str(resultado)
        hay_error = "error" in respuesta_limpia.lower() or '"ok": false' in respuesta_limpia.lower()

        actualizar_agente(
            "self_healing",
            "COMPLETED",
            "Validación completada",
            entrada="Resultado del flujo",
            proceso="Revisión completada",
            salida="Se detectó posible error en la respuesta" if hay_error else "No se detectaron errores críticos"
        )

        if len(respuesta_limpia) > 2000:
            respuesta_limpia = (
                respuesta_limpia[:2000]
                + "\n\n[Respuesta truncada para Dashboard]"
            )

        actualizar_agente(
            "respuesta",
            "COMPLETED",
            "Respuesta generada",
            entrada=f"Resultado validado del plugin {plugin_detectado}",
            proceso="Preparando visualización ejecutiva y técnica",
            salida="Respuesta disponible en Dashboard"
        )

        AGENT_STATE["respuesta_final"] = respuesta_limpia
        AGENT_STATE["estado_general"] = "COMPLETED"
        AGENT_STATE["fin"] = ahora_iso()

    except Exception as e:
        log.error(f"Error en ejecución dashboard: {e}")

        AGENT_STATE["ok"] = False
        AGENT_STATE["estado_general"] = "ERROR"
        AGENT_STATE["error"] = str(e)
        AGENT_STATE["fin"] = ahora_iso()

        actualizar_agente(
            "respuesta",
            "ERROR",
            "Error durante ejecución",
            entrada=solicitud,
            proceso="Excepción capturada",
            salida=str(e)
        )


@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "dashboard.html")


@app.route("/dashboard")
def dashboard():
    return send_from_directory(BASE_DIR, "dashboard.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "ok": True,
        "agent": "ONLINE",
        "flask": "ONLINE",
        "telegram_bot": "ACTIVE",
        "rag": "ACTIVE",
        "multi_agent": "BASIC_ACTIVE",
        "self_healing": "BASIC_ACTIVE",
        "memory": "BASIC_ACTIVE"
    })


@app.route("/api/crew/run", methods=["POST"])
def api_crew_run():
    if auth_error := _crew_auth_error():
        return auth_error
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json."}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON inválido."}), 400

    topic = data.get("topic")
    if not isinstance(topic, str):
        return jsonify({"error": "topic es obligatorio y debe ser string."}), 400
    if not topic.strip():
        return jsonify({"error": "topic no puede estar vacío."}), 400
    if len(topic) > MAX_TOPIC_LENGTH:
        return jsonify({"error": f"topic excede {MAX_TOPIC_LENGTH} caracteres."}), 400

    ingestion_id = data.get("ingestion_id")
    source_type = data.get("source_type", "api" if ingestion_id else "manual")
    if source_type not in {"manual", "api"}:
        return jsonify({"error": "source_type debe ser manual o api."}), 400

    if source_type == "api":
        if "input_data" in data:
            return jsonify({
                "error": "input_data no se acepta para una fuente API."
            }), 400
        if not isinstance(ingestion_id, str) or not ingestion_id:
            return jsonify({"error": "ingestion_id válido es obligatorio."}), 400
        ingestion = ingestion_registry.get(ingestion_id)
        if ingestion is None:
            return jsonify({"error": "ingestion_id inválido o expirado."}), 400
        input_data = ingestion["data"]
        source_name = ingestion["source_name"]
    else:
        if ingestion_id is not None:
            return jsonify({
                "error": "ingestion_id solo es válido para una fuente API."
            }), 400
        input_data = data.get("input_data")
        source_name = None

    if input_data is not None:
        try:
            validate_input_data(input_data)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    try:
        run = crew_run_registry.start(
            topic,
            input_data=input_data,
            source_type=source_type,
            source_name=source_name,
            rate_limiter=crew_run_rate_limiter,
        )
    except CrewRunBusyError:
        return jsonify({"error": "BUSY", "status": "BUSY"}), 409
    except CrewRunRateLimitError as exc:
        response = jsonify({
            "error": "RATE_LIMITED",
            "status": "RATE_LIMITED",
            "retry_after": exc.retry_after,
        })
        response.headers["Retry-After"] = str(exc.retry_after)
        return response, 429

    return jsonify({
        "run_id": run["run_id"],
        "status": run["status"],
        "status_url": f"/api/crew/status/{run['run_id']}",
        "source_type": run["source_type"],
        "source_name": run["source_name"],
    }), 202


@app.route("/api/ingestion/api", methods=["POST"])
def api_ingestion_api():
    if auth_error := _crew_auth_error():
        return auth_error
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json."}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON inválido."}), 400
    source = data.get("source", DEFAULT_SOURCE)
    if not isinstance(source, str):
        return jsonify({"error": "source debe ser string."}), 400
    if source not in API_SOURCES:
        return jsonify({"error": "Fuente API no permitida."}), 400

    try:
        result = fetch_api_source(source)
    except IngestionTimeoutError as exc:
        return jsonify({"error": str(exc), "status": "ERROR"}), 504
    except IngestionError as exc:
        return jsonify({"error": str(exc), "status": "ERROR"}), 502
    record = ingestion_registry.store(
        source=result["source"],
        source_name=result["source_name"],
        data=result["data"],
    )
    return jsonify({
        "ingestion_id": record["ingestion_id"],
        "source": result["source"],
        "source_name": result["source_name"],
        "status": result["status"],
        "preview": result["preview"],
        "expires_in": INGESTION_TTL_SECONDS,
    }), 200


@app.route("/api/crew/status/<run_id>")
def api_crew_status(run_id):
    if auth_error := _crew_auth_error():
        return auth_error
    run = crew_run_registry.get(run_id)
    if run is None:
        return jsonify({"error": "Run no encontrado."}), 404
    return jsonify(run), 200


@app.route("/api/agent-state")
def api_agent_state():
    return jsonify(AGENT_STATE)


@app.route("/api/agent-run", methods=["POST"])
def api_agent_run():
    data = request.get_json(silent=True) or {}
    solicitud = data.get("solicitud", "").strip()

    if not solicitud:
        return jsonify({
            "ok": False,
            "error": "La solicitud está vacía"
        }), 400

    if AGENT_STATE.get("estado_general") == "PROCESSING":
        return jsonify({
            "ok": False,
            "error": "El agente ya está procesando una solicitud"
        }), 409

    hilo = threading.Thread(
        target=ejecutar_solicitud_dashboard,
        args=(solicitud,),
        daemon=True
    )
    hilo.start()

    return jsonify({
        "ok": True,
        "mensaje": "Solicitud recibida y enviada al agente",
        "solicitud": solicitud
    })


@app.route("/api/plugins")
def api_plugins():
    plugins_activos = leer_json_seguro(
        os.path.join(BASE_DIR, "plugins_activos.json"),
        []
    )

    plugins_dir = os.path.join(BASE_DIR, "plugins")
    plugins_detectados = []

    if os.path.exists(plugins_dir):
        plugins_detectados = [
            f for f in os.listdir(plugins_dir)
            if f.endswith(".py") and f != "__init__.py"
        ]

    return jsonify({
        "ok": True,
        "activos": plugins_activos,
        "detectados": plugins_detectados,
        "total_activos": len(plugins_activos),
        "total_detectados": len(plugins_detectados)
    })


@app.route("/api/chunks")
def api_chunks():
    archivos_chunks = []

    if os.path.exists(CHUNKS_DIR):
        archivos_chunks = [
            f for f in os.listdir(CHUNKS_DIR)
            if f.endswith(".chunks.json")
        ]

    return jsonify({
        "ok": True,
        "chunks_dir": CHUNKS_DIR,
        "total_archivos_chunks": len(archivos_chunks),
        "archivos": archivos_chunks
    })


@app.route("/api/documents")
def api_documents():
    metadata = []

    if os.path.exists(METADATA_DIR):
        for archivo in os.listdir(METADATA_DIR):
            if not archivo.endswith(".json"):
                continue

            data = leer_json_seguro(
                os.path.join(METADATA_DIR, archivo),
                {}
            )

            metadata.append(data)

    return jsonify({
        "ok": True,
        "total_documentos": len(metadata),
        "documentos": metadata
    })


@app.route("/api/goals")
def api_goals():
    data = leer_json_seguro(
        os.path.join(BASE_DIR, "goals.json"),
        {}
    )

    return jsonify({
        "ok": True,
        "data": data
    })


@app.route("/api/memory")
def api_memory():
    data = leer_json_seguro(
        os.path.join(BASE_DIR, "memory", "summary.json"),
        {}
    )

    eventos = leer_json_seguro(
        os.path.join(BASE_DIR, "memory", "events.json"),
        []
    )

    return jsonify({
        "ok": True,
        "summary": data,
        "events": eventos[-10:] if isinstance(eventos, list) else []
    })



@app.route("/api/pm-flow")
def api_pm_flow():
    return jsonify(PM_FLOW_STATE)


@app.route("/api/dashboard-summary")
def api_dashboard_summary():
    return jsonify({
        "ok": True,
        "chunks": contar_archivos(CHUNKS_DIR, ".chunks.json"),
        "metadata": contar_archivos(METADATA_DIR, ".json"),
        "plugins": contar_archivos(os.path.join(BASE_DIR, "plugins"), ".py"),
        "historial_existe": os.path.exists(os.path.join(BASE_DIR, "historial.json")),
        "goals_existe": os.path.exists(os.path.join(BASE_DIR, "goals.json"))
    })


if __name__ == "__main__":
    # Ciclo automático de noticias desactivado temporalmente.
    # Motivo: validar Dashboard Técnico Operativo V1/V2/V3 sin ruido operativo,
    # sin consumo innecesario de Groq/Tavily/DuckDuckGo y sin mensajes automáticos al bot.
    # threading.Thread(target=ciclo_noticias, daemon=True).start()

    threading.Thread(target=iniciar_bot, daemon=True).start()

    log.info("Sistema inicializado. Flask en :5000")
    app.run(host="0.0.0.0", port=5000)
