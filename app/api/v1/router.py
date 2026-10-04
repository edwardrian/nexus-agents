from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

from app.agent.graph import get_agent_app

router = APIRouter(prefix="/chat", tags=["Chat & Agents"])


class ChatMessage(BaseModel):
    role: str = Field(description="Tipo de mensaje: human (usuario) o ai (agente)", examples=["human"])
    content: str = Field(description="Texto del mensaje", examples=["Hoy terminé el informe"])


class SessionHistory(BaseModel):
    session_id: str = Field(description="ID del hilo de memoria", examples=["telegram-123456789"])
    messages: list[ChatMessage] = Field(description="Mensajes en orden cronológico")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "telegram-123456789",
                    "messages": [
                        {"role": "human", "content": "Hoy terminé el informe"},
                        {"role": "ai", "content": "Anotado: informe terminado. ¿Algo pendiente?"},
                    ],
                }
            ]
        }
    }


@router.get(
    "/sessions/{session_id}/history",
    response_model=SessionHistory,
    summary="Obtener historial de la sesión",
    responses={200: {"description": "Historial de la sesión (lista vacía si no existe)"}},
)
async def get_session_history(
    session_id: str = Path(
        description='ID de la sesión. En Telegram: "telegram-<user_id>"',
        examples=["telegram-123456789"],
    ),
):
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
        {"role": msg.type, "content": msg.text}
        for msg in state.values.get("messages", [])
    ]
    return {"session_id": session_id, "messages": history}
