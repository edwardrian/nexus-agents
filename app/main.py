from contextlib import asynccontextmanager
from app.db.checkpoint import init_db, close_db

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as chat_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Se ejecuta al iniciar la aplicación (con el event loop ya activo)
    await init_db()
    yield
    # Se ejecuta al apagar la aplicación
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url=None,       # Desactiva Swagger UI (/docs)
    redoc_url=None,      # Desactiva ReDoc (/redoc)
    openapi_url=None,    # Desactiva el endpoint del schema JSON (/openapi.json)
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

# Raíz limpia
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
    }

# Endpoint de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
    }

# Rutas bajo /api/v1
app.include_router(chat_router, prefix="/api/v1")