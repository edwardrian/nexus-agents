import traceback

from langchain_core.messages import HumanMessage
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.agent.graph import get_agent_app
from app.core.config import settings

# Límite de caracteres por mensaje en Telegram
TELEGRAM_MAX_LENGTH = 4096


def is_allowed(user_id: int) -> bool:
    """Si no hay IDs configurados, cualquiera puede usar el bot."""
    allowed = settings.telegram_allowed_ids
    return not allowed or user_id in allowed


def split_message(text: str, limit: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Divide un texto largo en trozos que Telegram acepte."""
    return [text[i:i + limit] for i in range(0, len(text), limit)] or [""]


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start."""
    if not is_allowed(update.effective_user.id):
        return
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Hola {user_name}, Nexus está listo.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el mensaje al agente de LangGraph y responde con su resultado."""
    user_id = update.effective_user.id
    user_text = update.message.text

    print(f"[telegram] {user_id}: {user_text}")
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        result = await get_agent_app().ainvoke(
            {"messages": [HumanMessage(content=user_text)]},
            # Un hilo de memoria por usuario de Telegram
            config={"configurable": {"thread_id": f"telegram-{user_id}"}},
        )
        # .text extrae solo el texto (sirve si el contenido es str o lista de bloques)
        reply = result["messages"][-1].text
    except Exception:
        traceback.print_exc()
        reply = "Ocurrió un error al procesar tu mensaje. Intenta de nuevo."

    for chunk in split_message(reply or "(sin respuesta)"):
        await update.message.reply_text(chunk)
