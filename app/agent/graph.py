from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.state import CompiledStateGraph

from app.agent.state import AgentState
from app.services.llm_factory import get_llm
from app.db.checkpoint import get_checkpointer

# 1. Definir o importar las herramientas (tools) que el agente puede usar
# Por ahora creamos una de ejemplo directamente aquí:
from langchain_core.tools import tool

@tool
def get_system_status(service_name: str) -> str:
    """Consulta el estado operativo de un servicio."""
    return f"Servicio '{service_name}': OPERATIVO, CPU al 24%, 0 errores."

tools = [get_system_status]

# 2. Inicializar el LLM (Ollama, Gemini o Bedrock según tu factory) y asociarle las tools
llm = get_llm().bind_tools(tools)

# 3. Definir el nodo del agente (el que piensa y decide)
async def call_model(state: AgentState):
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}

# 4. Función condicional: ¿el modelo generó respuesta o pidió ejecutar una tool?
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# 5. Armar el StateGraph
workflow = StateGraph(AgentState)

# Agregar los nodos
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Definir el punto de inicio y las conexiones (edges)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})
workflow.add_edge("tools", "agent")  # Luego de ejecutar la tool, vuelve al agente para que responda

# 6. Compilar el grafo con el checkpointer de Supabase
_agent_app: Optional[CompiledStateGraph] = None

def get_agent_app() -> CompiledStateGraph:
    global _agent_app
    if _agent_app is None:
        checkpointer = get_checkpointer()
        _agent_app = workflow.compile(checkpointer=checkpointer)
    return _agent_app