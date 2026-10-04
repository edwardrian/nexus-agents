import asyncio
from contextlib import asynccontextmanager

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import graph, tools


class FakeCursor:
    async def fetchone(self):
        return (1,)


class FakeConnection:
    def __init__(self, executed):
        self.executed = executed

    async def execute(self, sql, params):
        self.executed.append(params)
        return FakeCursor()


class FakePool:
    """Reemplaza el pool de Supabase y guarda los parámetros de cada INSERT."""

    def __init__(self):
        self.executed = []

    @asynccontextmanager
    async def connection(self):
        yield FakeConnection(self.executed)


@pytest.fixture
def fake_pool(monkeypatch):
    pool = FakePool()
    monkeypatch.setattr(tools, "pool", pool)
    return pool


def test_el_llm_no_ve_user_id_ni_config():
    args = tools.save_purchase.tool_call_schema.model_json_schema()["properties"]
    assert "config" not in args
    assert "user_id" not in args
    assert {"description", "amount"} <= set(args)


def test_save_purchase_usa_el_thread_id(fake_pool):
    result = asyncio.run(tools.save_purchase.ainvoke(
        {"description": "Leche", "amount": 2.5, "purchased_at": "2026-10-03"},
        config={"configurable": {"thread_id": "telegram-123"}},
    ))
    assert "id 1" in result
    user_id, description, amount, currency, *_ , day = fake_pool.executed[0]
    assert (user_id, description, amount, currency) == ("telegram-123", "Leche", 2.5, "USD")
    assert day.isoformat() == "2026-10-03"


def test_save_purchase_rechaza_fecha_invalida(fake_pool):
    result = asyncio.run(tools.save_purchase.ainvoke(
        {"description": "Pan", "amount": 1, "purchased_at": "ayer"},
        config={"configurable": {"thread_id": "telegram-123"}},
    ))
    assert result.startswith("Error")
    assert fake_pool.executed == []


def test_grafo_guarda_la_compra_y_confirma(fake_pool, monkeypatch):
    # 1ª respuesta: el LLM pide guardar la compra. 2ª: confirma al usuario.
    fake_llm = GenericFakeChatModel(messages=iter([
        AIMessage(content="", tool_calls=[{
            "name": "save_purchase",
            "args": {"description": "Pan", "amount": 1.25},
            "id": "call_1",
        }]),
        AIMessage(content="Listo, registré Pan por 1.25 USD."),
    ]))
    monkeypatch.setattr(graph, "llm", fake_llm)

    app = graph.workflow.compile(checkpointer=InMemorySaver())
    result = asyncio.run(app.ainvoke(
        {"messages": [HumanMessage(content="Compré pan por 1.25")]},
        config={"configurable": {"thread_id": "telegram-123"}},
    ))

    assert fake_pool.executed[0][:3] == ("telegram-123", "Pan", 1.25)
    assert [m.type for m in result["messages"]] == ["human", "ai", "tool", "ai"]
    assert result["messages"][-1].text == "Listo, registré Pan por 1.25 USD."


def test_router_sin_tool_calls_termina():
    state = {"messages": [AIMessage(content="Hola")]}
    assert graph.route_after_agent(state) == "__end__"
