from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configuración general
    PROJECT_NAME: str = "nexus-agents"

    # Proveedor de LLM ("gemini", "bedrock", "ollama")
    LLM_PROVIDER: str = "ollama"

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # AWS Bedrock
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()