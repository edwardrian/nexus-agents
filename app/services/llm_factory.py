# app/services/llm_factory.py
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm():
    provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()

    if provider == "bedrock":
        from langchain_aws import ChatBedrockConverse
        return ChatBedrockConverse(
            model=settings.BEDROCK_MODEL_ID,
            region_name=settings.AWS_REGION
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="llama3.2:latest")
    else:
        # Importante: pasar api_key desde settings
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            api_key=settings.GEMINI_API_KEY
        )