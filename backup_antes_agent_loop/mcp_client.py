"""
mcp_client.py — Cliente del agente.
Mantiene su propia lógica de gestión (crear/reparar plugins, instalar librerías)
pero comparte las herramientas base desde herramientas.py.
"""

import json
from groq import Groq

from herramientas import (
    GROQ_API_KEY,
    MODELO,
    TOOLS,
    ejecutar_herramienta,
)

# ── Cliente Groq ──────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT_CLIENTE = (
    "ERES EL CEREBRO DE GESTIÓN. TIENES ACCESO A HERRAMIENTAS DE SISTEMA. "
    "CUANDO EL USUARIO PIDA 'CREAR', 'REPARAR' O 'INSTALAR', DEBES USAR "
    "LAS TOOLS 'crear_plugin', 'autocura_plugin' O 'instalar_libreria'. "
    "LUEGO DE EJECUTAR CUALQUIER COMANDO, RESPONDE AL USUARIO CONFIRMANDO EL RESULTADO."
)


def procesar_cliente(user_input: str, chat_id=None) -> str:
    """
    Versión cliente del agente. Sin historial persistente (stateless).
    Útil para llamadas programáticas o testing.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_CLIENTE},
        {"role": "user",   "content": user_input},
    ]

    response = client.chat.completions.create(
        model=MODELO,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            resultado = ejecutar_herramienta(tool_call.function.name, args)
            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "name":         tool_call.function.name,
                "content":      str(resultado),
            })

        final = client.chat.completions.create(model=MODELO, messages=messages)
        return final.choices[0].message.content

    return msg.content or "Procesado sin texto."
