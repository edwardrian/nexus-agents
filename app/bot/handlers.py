from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Hola {user_name}, Nexus está listo.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto entrantes."""
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # Aquí es donde más adelante invocas tu grafo de LangGraph:
    # response = await my_langgraph_agent.ainvoke({"messages": [user_text]}, config={"configurable": {"thread_id": str(user_id)}})
    
    await update.message.reply_text(f"Recibido: {user_text}")