import telebot
bot = telebot.TeleBot('8794010381:AAFlPjFXjD3QEoHw6geTvDKIVPWIWS6wBG0')

@bot.message_handler(func=lambda message: True)
def responder(message):
    print(f"¡ENCONTRADO! Tu CHAT_ID es: {message.chat.id}")
    bot.reply_to(message, f"Tu ID es: {message.chat.id}")

print("Bot listo. Escribe 'hola' en Telegram ahora...")
bot.infinity_polling()
