from fastapi import APIRouter

from app.agent.graph import get_agent_app

router = APIRouter(prefix="/chat", tags=["Chat & Agents"])


@router.get("/sessions/{session_id}/history", summary="Obtener historial de la sesión")
async def get_session_history(session_id: str):
    """
    Recupera los mensajes almacenados en los checkpoints de Supabase
    para un session_id determinado (en Telegram: "telegram-<user_id>").
    """
    config = {"configurable": {"thread_id": session_id}}
    state = await get_agent_app().aget_state(config)

    if not state or not state.values:
        return {"session_id": session_id, "messages": []}

    # Formateamos los mensajes serializados
    history = [
        {"role": msg.type, "content": msg.content}
        for msg in state.values.get("messages", [])
    ]
    return {"session_id": session_id, "messages": history}
