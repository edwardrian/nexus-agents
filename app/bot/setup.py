import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.bot.handlers import start_handler, message_handler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def build_telegram_app():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN no está definido en el entorno.")
        
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Registrar handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    return app

# Instancia singleton lista para importar
telegram_app = build_telegram_app()