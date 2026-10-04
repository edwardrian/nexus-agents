from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as chat_router
from app.bot.setup import telegram_app
from app.core.config import settings
from app.db.checkpoint import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Iniciar persistencia de LangGraph en Postgres
    await init_db()

    # 2. Iniciar bot de Telegram en segundo plano (solo si hay token)
    if telegram_app:
        await telegram_app.initialize()
        await telegram_app.start()

        # Limpiar webhooks previos y arrancar Long Polling
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        await telegram_app.updater.start_polling()

    yield

    # 3. Detener bot de Telegram limpiamente
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

    # 4. Cerrar conexiones a base de datos
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API de Nexus: consulta del historial de conversaciones del agente.",
    docs_url="/docs",    # Swagger UI
    redoc_url=None,      # Desactiva ReDoc (/redoc)
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
    }


# Rutas bajo /api/v1
app.include_router(chat_router, prefix="/api/v1")