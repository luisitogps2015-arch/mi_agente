import threading, time, logging, os
from flask import Flask
import telebot
from groq import Groq
from herramientas import TELEGRAM_TOKEN, CHAT_ID, buscar_en_web_real
from mcp_server import procesar_agente

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
SALUDOS = {"hola","hi","buenas","buenos dias","buenas tardes","saludos"}

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if message.text.lower().strip() in SALUDOS:
        bot.reply_to(message, "Hola! En que puedo ayudarte?")
        return
    try:
        bot.reply_to(message, procesar_agente(message.text, message.chat.id))
    except Exception as e:
        bot.reply_to(message, "Error al procesar la solicitud.")

def ciclo_noticias():
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY",""))
    log.info("Ciclo de noticias iniciado.")
    time.sleep(60)
    while True:
        try:
            texto = buscar_en_web_real("noticias inteligencia artificial Ecuador")
            if texto and "Error" not in texto:
                resp = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":f"Resume en 3 puntos clave:\n{texto}"}]
                )
                bot.send_message(CHAT_ID, f"RESUMEN AUTOMATICO:\n\n{resp.choices[0].message.content}")
                log.info("Resumen enviado.")
        except Exception as e:
            log.error(f"Error ciclo noticias: {e}")
        time.sleep(3600)

def iniciar_bot():
    bot.infinity_polling(timeout=60, long_polling_timeout=60, none_stop=True)

@app.route("/health")
def health():
    return {"status":"ok"}, 200

if __name__ == "__main__":
    threading.Thread(target=ciclo_noticias, daemon=True).start()
    threading.Thread(target=iniciar_bot, daemon=True).start()
    log.info("Sistema inicializado. Flask en :5000")
    app.run(host="0.0.0.0", port=5000)
