"""
noticias_agente.py — Ciclo automático de noticias.
Busca con Tavily, resume con Groq y envía por Telegram.
"""

import sys
import time
import logging
import telebot
from groq import Groq

from herramientas import (
    GROQ_API_KEY,
    TELEGRAM_TOKEN,
    CHAT_ID,
    MODELO,
    buscar_en_web_real,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)
bot    = telebot.TeleBot(TELEGRAM_TOKEN)


def obtener_resumen_ia(query: str = "Noticias Mafias Ecuador") -> str:
    log.info(f"Buscando: {query}")
    texto = buscar_en_web_real(query)
    if "Error" in texto or not texto:
        return "No se pudieron obtener noticias en este momento."

    prompt = (
        "Eres un analista experto. Resume estas noticias en 3 puntos clave "
        f"con tono profesional:\n{texto}"
    )
    resp = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def ejecutar_ciclo():
    resumen = obtener_resumen_ia()
    if resumen and "Error" not in resumen:
        try:
            bot.send_message(CHAT_ID, f"🤖 RESUMEN:\n\n{resumen}")
            log.info("Resumen enviado a Telegram.")
        except Exception as e:
            log.error(f"Error enviando a Telegram: {e}")
    else:
        log.warning(f"Ciclo fallido: {resumen}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        log.info("Modo prueba: ejecutando una vez.")
        ejecutar_ciclo()
    else:
        log.info("Modo automático: cada 1 hora.")
        while True:
            ejecutar_ciclo()
            time.s
