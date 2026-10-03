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

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    # IDs de usuario permitidos, separados por coma (vacío = cualquiera)
    TELEGRAM_ALLOWED_USER_IDS: str = ""

    @property
    def telegram_allowed_ids(self) -> set[int]:
        return {int(x) for x in self.TELEGRAM_ALLOWED_USER_IDS.split(",") if x.strip()}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()