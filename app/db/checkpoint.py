import os
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings

db_uri = getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL")

if not db_uri:
    raise ValueError(
        "CRÍTICO: 'DATABASE_URL' no está definida o está vacía. "
        "Asegúrate de configurarla en tu archivo .env con la URI de Supabase."
    )

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": None,  # Vital para el pooler de Supabase
}

# 1. Pool asíncrono (crearlo con open=False no requiere loop activo)
pool = AsyncConnectionPool(
    conninfo=db_uri,
    max_size=10,
    kwargs=connection_kwargs,
    open=False,
)

# 2. Variable global para el checkpointer
_checkpointer: Optional[AsyncPostgresSaver] = None


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError(
            "El checkpointer no ha sido inicializado. "
            "Asegúrate de que init_db() se ejecutó en el lifespan."
        )
    return _checkpointer


async def init_db():
    global _checkpointer
    await pool.open()
    # Se instancia aquí, cuando el loop de FastAPI ya está corriendo
    _checkpointer = AsyncPostgresSaver(pool)
    # Opcional pero recomendado por LangGraph para crear tablas si no existen:
    await _checkpointer.setup()


async def close_db():
    await pool.close()