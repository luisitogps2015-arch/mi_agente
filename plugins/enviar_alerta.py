import sqlite3
import telebot

def run(params):
    mensaje = params.get('mensaje', 'Sin mensaje')

    # 1. ENVIAR A TELEGRAM PRIMERO (Prioridad)
    try:
        TOKEN = "8794010381:AAFlPjFXjD3QEoHw6geTvDKIVPWIWS6wBG0"
        CHAT_ID = "8419346499"
        bot = telebot.TeleBot(TOKEN)
        bot.send_message(CHAT_ID, f"🔔 ALERTA:\n\n{mensaje}")
        resultado_tel = "Enviado a Telegram"
    except Exception as e:
        resultado_tel = f"Error Telegram: {str(e)}"

    # 2. GUARDAR EN DB DESPUÉS (Si falla, no importa)
    try:
        conn = sqlite3.connect('/app/agente_data.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS alertas_sistema (id INTEGER PRIMARY KEY AUTOINCREMENT, mensaje TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
        cursor.execute('INSERT INTO alertas_sistema (mensaje) VALUES (?)', (mensaje,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass # Ignoramos el error de solo lectura

    return resultado_tel
