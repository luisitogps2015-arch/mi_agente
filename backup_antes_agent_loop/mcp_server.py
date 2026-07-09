import json
import traceback
from groq import Groq

from herramientas import (
    GROQ_API_KEY,
    TOOLS,
    ejecutar_herramienta,
    guardar_mensaje,
    cargar_historial,
    registrar_error,
    init_db,
)

MODELO_TOOLS  = "llama-3.3-70b-versatile"
MODELO_RAPIDO = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Eres un agente tecnico con acceso a herramientas externas.
REGLAS: 1. Si piden noticias o info reciente DEBES llamar a buscar_internet, NUNCA respondas desde tu memoria.
2. Para plugins usa crear_plugin o autocura_plugin.
3. Para librerias usa instalar_libreria.
4. Incluye siempre los links encontrados en tu respuesta."""

PALABRAS_BUSQUEDA = ["busca","noticias","noticia","informacion","reciente","hoy","ultimas","buscar","investiga","encuentra"]

def procesar_agente(user_input: str, chat_id) -> str:
    guardar_mensaje(chat_id, "user", user_input)
    historial = cargar_historial(chat_id, limite=10)
    messages  = [{"role": "system", "content": SYSTEM_PROMPT}] + historial
    texto_lower = user_input.lower()
    requiere_busqueda = any(p in texto_lower for p in PALABRAS_BUSQUEDA)
    tool_choice = {"type": "function", "function": {"name": "buscar_internet"}} if requiere_busqueda else "auto"
    try:
        response = client.chat.completions.create(
            model=MODELO_TOOLS, messages=messages, tools=TOOLS,
            tool_choice=tool_choice, temperature=0.0, parallel_tool_calls=False,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                    resultado = ejecutar_herramienta(tool_call.function.name, args)
                except Exception as e:
                    resultado = f"Error ejecutando herramienta: {e}"
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": tool_call.function.name, "content": str(resultado)})
            final = client.chat.completions.create(model=MODELO_RAPIDO, messages=messages, temperature=0.0)
            respuesta = final.choices[0].message.content or "Procesado sin texto."
        else:
            respuesta = msg.content if msg.content else "Procesado sin texto."
        guardar_mensaje(chat_id, "assistant", respuesta)
        return respuesta
    except Exception as e:
        traceback.print_exc()
        registrar_error({"error": str(e), "input": user_input, "chat_id": str(chat_id)})
        return f"Error interno del agente: {e}"

init_db()
