from datetime import date
from typing import Optional

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.services.llm_factory import get_llm
from app.db.checkpoint import get_checkpointer

# 1. Inicializar el LLM (Ollama o Gemini según LLM_PROVIDER)
llm = get_llm()

# 2. Definir el nodo del agente (el que responde)
async def call_model(state: AgentState):
    # El system prompt no se guarda en el historial: se antepone en cada llamada
    system = SystemMessage(content=SYSTEM_PROMPT.format(today=date.today().isoformat()))
    response = await llm.ainvoke([system, *state["messages"]])
    return {"messages": [response]}

# 3. Armar el StateGraph: un solo nodo que responde y termina
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# 4. Compilar el grafo con el checkpointer de Supabase
_agent_app: Optional[CompiledStateGraph] = None

def get_agent_app() -> CompiledStateGraph:
    global _agent_app
    if _agent_app is None:
        checkpointer = get_checkpointer()
        _agent_app = workflow.compile(checkpointer=checkpointer)
    return _agent_app
