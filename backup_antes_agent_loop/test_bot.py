import telebot
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)
try:
    bot.send_message(CHAT_ID, "Prueba de conexión exitosa.")
    print("¡Mensaje enviado correctamente!")
except Exception as e:
    print(f"Error al enviar: {e}")
