from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.api.v1.sse import agent_event_generator
from app.agent.graph import agent_app

router = APIRouter(prefix="/chat", tags=["Chat & Agents"])

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="Mensaje o instrucción del usuario", min_length=1)
    session_id: str = Field(..., description="ID de sesión / thread_id para persistencia en Supabase")

@router.post("/stream", summary="Interactuar con el agente en tiempo real")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Inicia una ejecución del agente.
    Devuelve un flujo SSE continuo con eventos:
    - `token`: trozos de texto generados.
    - `tool_start`: notificación de herramienta invocada.
    - `tool_end`: resultado de la herramienta.
    - `done`: fin del turno de ejecución.
    """
    return StreamingResponse(
        agent_event_generator(request.prompt, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Evita que NGINX o proxies retengan los paquetes SSE
        }
    )

@router.get("/sessions/{session_id}/history", summary="Obtener historial de la sesión")
async def get_session_history(session_id: str):
    """
    Recupera los mensajes almacenados en los checkpoints de Supabase
    para un session_id determinado.
    """
    config = {"configurable": {"thread_id": session_id}}
    state = agent_app.get_state(config)
    
    if not state or not state.values:
        return {"session_id": session_id, "messages": []}
    
    # Formateamos los mensajes serializados
    history = [
        {"role": msg.type, "content": msg.content}
        for msg in state.values.get("messages", [])
    ]
    return {"session_id": session_id, "messages": history}