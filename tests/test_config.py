import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.fixture(autouse=True)
def limpiar_entorno(monkeypatch):
    # Que las variables del sistema o de CI no afecten a estos tests
    for name in ["LLM_PROVIDER", "OLLAMA_MODEL", "GEMINI_MODEL", "GEMINI_API_KEY"]:
        monkeypatch.delenv(name, raising=False)


def make_settings(**values):
    # _env_file=None: no leer el .env local en los tests
    return Settings(_env_file=None, **values)


def test_ollama_requiere_modelo_pero_no_token():
    with pytest.raises(ValidationError, match="OLLAMA_MODEL"):
        make_settings(LLM_PROVIDER="ollama")
    assert make_settings(LLM_PROVIDER="ollama", OLLAMA_MODEL="llama3.2:latest").OLLAMA_MODEL == "llama3.2:latest"


def test_gemini_requiere_modelo_y_api_key():
    with pytest.raises(ValidationError, match="GEMINI_MODEL, GEMINI_API_KEY"):
        make_settings(LLM_PROVIDER="gemini")
    settings = make_settings(LLM_PROVIDER="gemini", GEMINI_MODEL="gemini-2.5-flash", GEMINI_API_KEY="key")
    assert settings.GEMINI_API_KEY == "key"


def test_provider_invalido():
    with pytest.raises(ValidationError):
        make_settings(LLM_PROVIDER="bedrock")
