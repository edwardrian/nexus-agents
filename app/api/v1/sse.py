import json
import traceback
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from app.agent.graph import get_agent_app


async def agent_event_generator(prompt: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    Ejecuta el grafo de LangGraph y emite los eventos en formato SSE.
    """
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {"messages": [HumanMessage(content=prompt)]}

    try:
        agent_app = get_agent_app()
        async for event in agent_app.astream_events(input_data, config=config, version="v2"):
            kind = event.get("event")

            print(kind)

            # Emisión de tokens de texto generados por el LLM
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    # En algunos proveedores content es una lista o dict
                    content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                    data = json.dumps({"type": "token", "content": content})
                    yield f"data: {data}\n\n"

            # Notificación cuando el agente decide llamar a una herramienta
            elif kind == "on_tool_start":
                data = json.dumps({
                    "type": "tool_start",
                    "tool": event.get("name"),
                    "input": event.get("data", {}).get("input")
                })
                yield f"data: {data}\n\n"

            # Resultado retornado por la herramienta
            elif kind == "on_tool_end":
                data = json.dumps({
                    "type": "tool_end",
                    "output": str(event.get("data", {}).get("output"))
                })
                yield f"data: {data}\n\n"

        # Fin del turno
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as exc:
        # Muestra el error exacto en la terminal de Uvicorn para diagnosticar
        print("=== Error en agent_event_generator ===")
        traceback.print_exc()

        err_data = json.dumps({"type": "error", "message": str(exc)})
        yield f"data: {err_data}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"