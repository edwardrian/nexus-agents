import os
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

# 1. Pool asíncrono
pool = AsyncConnectionPool(
    conninfo=db_uri,
    max_size=10,
    kwargs=connection_kwargs,
    open=True,
)

# 2. Instancia del checkpointer asíncrono
_checkpointer = AsyncPostgresSaver(pool)


def get_checkpointer() -> AsyncPostgresSaver:
    return _checkpointer