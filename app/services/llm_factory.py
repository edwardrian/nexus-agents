# app/services/llm_factory.py
from app.core.config import settings


def get_llm():
    """Crea el LLM según LLM_PROVIDER. Cada librería se importa solo si se usa."""
    if settings.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL)

    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, api_key=settings.GEMINI_API_KEY)
