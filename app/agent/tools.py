from datetime import date
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.db.checkpoint import pool

INSERT_PURCHASE_SQL = """
    INSERT INTO public.purchases
        (user_id, description, amount, currency, quantity, category, store, purchased_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
"""


@tool
async def save_purchase(
    description: str,
    amount: float,
    config: RunnableConfig,
    currency: str = "USD",
    quantity: int = 1,
    category: Optional[str] = None,
    store: Optional[str] = None,
    purchased_at: Optional[str] = None,
) -> str:
    """Guarda una compra que hizo el usuario.

    Args:
        description: Qué compró, por ejemplo "Leche y pan".
        amount: Monto total pagado, por ejemplo 4.50.
        currency: Código ISO de la moneda, por ejemplo "USD".
        quantity: Cantidad de unidades compradas.
        category: Categoría: comida, transporte, hogar, salud, ocio, ropa, servicios u otros.
        store: Tienda o lugar donde compró.
        purchased_at: Fecha de la compra en formato YYYY-MM-DD. Si no se indica, es hoy.
    """
    if amount < 0:
        return "Error: el monto no puede ser negativo."
    if quantity < 1:
        return "Error: la cantidad debe ser mayor a 0."
    try:
        day = date.fromisoformat(purchased_at) if purchased_at else date.today()
    except ValueError:
        return "Error: la fecha debe tener el formato YYYY-MM-DD."

    # El usuario sale del thread_id ("telegram-<user_id>"), nunca del LLM
    user_id = config["configurable"]["thread_id"]

    async with pool.connection() as conn:
        cursor = await conn.execute(
            INSERT_PURCHASE_SQL,
            (user_id, description, amount, currency.upper(), quantity, category, store, day),
        )
        row = await cursor.fetchone()

    return f"Compra guardada (id {row[0]}): {description}, {amount:.2f} {currency.upper()}, {day.isoformat()}."


TOOLS = [save_purchase]
