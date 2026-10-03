from typing import Optional

from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters

from app.bot.handlers import message_handler, start_handler
from app.core.config import settings


def build_telegram_app() -> Optional[Application]:
    # Sin token (por ejemplo en tests o CI) la API arranca sin el bot
    if not settings.TELEGRAM_BOT_TOKEN:
        print("[telegram] TELEGRAM_BOT_TOKEN no definido: el bot no se iniciará.")
        return None

    if not settings.telegram_allowed_ids:
        print("[telegram] AVISO: TELEGRAM_ALLOWED_USER_IDS vacío, cualquiera puede usar el bot.")

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Registrar handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    return app


# Instancia singleton lista para importar (None si no hay token)
telegram_app = build_telegram_app()
