from typing import Literal, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Variables obligatorias (en el .env) según el proveedor de LLM elegido
REQUIRED_BY_PROVIDER = {
    "ollama": ["OLLAMA_MODEL"],  # corre local, no necesita token
    "gemini": ["GEMINI_MODEL", "GEMINI_API_KEY"],
}


class Settings(BaseSettings):
    # Configuración general
    PROJECT_NAME: str = "nexus-agents"
    DATABASE_URL: Optional[str] = None

    # Proveedor de LLM
    LLM_PROVIDER: Literal["ollama", "gemini"] = "ollama"

    # Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: Optional[str] = None

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: Optional[str] = None

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    # IDs de usuario permitidos, separados por coma (vacío = cualquiera)
    TELEGRAM_ALLOWED_USER_IDS: str = ""

    @property
    def telegram_allowed_ids(self) -> set[int]:
        return {int(x) for x in self.TELEGRAM_ALLOWED_USER_IDS.split(",") if x.strip()}

    @model_validator(mode="after")
    def check_provider_settings(self):
        # Falla al arrancar si falta algo que el proveedor elegido necesita
        missing = [name for name in REQUIRED_BY_PROVIDER[self.LLM_PROVIDER] if not getattr(self, name)]
        if missing:
            raise ValueError(f"LLM_PROVIDER={self.LLM_PROVIDER} requiere: {', '.join(missing)}")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
