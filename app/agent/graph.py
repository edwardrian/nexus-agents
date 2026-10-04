from datetime import date
from typing import Literal, Optional

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.agent.tools import TOOLS
from app.services.llm_factory import get_llm
from app.db.checkpoint import get_checkpointer

# 1. Inicializar el LLM (Ollama o Gemini según LLM_PROVIDER) con sus herramientas
llm = get_llm().bind_tools(TOOLS)

# 2. Definir el nodo del agente (decide si responde o llama a una herramienta)
async def call_model(state: AgentState):
    # El system prompt no se guarda en el historial: se antepone en cada llamada
    system = SystemMessage(content=SYSTEM_PROMPT.format(today=date.today().isoformat()))
    response = await llm.ainvoke([system, *state["messages"]])
    return {"messages": [response]}

# 3. Router: si el LLM pidió una herramienta, ir a guardar la compra; si no, terminar
def route_after_agent(state: AgentState) -> Literal["save_purchase", "__end__"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "save_purchase"
    return END

# 4. Armar el StateGraph: agent ⇄ save_purchase
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("save_purchase", ToolNode(TOOLS))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", route_after_agent)
# Tras guardar, vuelve al agente para que confirme al usuario
workflow.add_edge("save_purchase", "agent")

# 5. Compilar el grafo con el checkpointer de Supabase
_agent_app: Optional[CompiledStateGraph] = None

def get_agent_app() -> CompiledStateGraph:
    global _agent_app
    if _agent_app is None:
        checkpointer = get_checkpointer()
        _agent_app = workflow.compile(checkpointer=checkpointer)
    return _agent_app
