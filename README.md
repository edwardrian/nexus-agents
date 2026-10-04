# nexus-agents

Asistente de tareas por **Telegram** construido con **FastAPI** y **LangGraph**. Registra las tareas realizadas y pendientes del usuario y recuerda cada conversación guardándola en **Supabase (PostgreSQL)**.

## Stack

| Pieza | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Bot | python-telegram-bot (long polling) |
| Agente | LangGraph (`StateGraph` con un nodo) |
| LLM | Ollama (local) o Google Gemini — configurable |
| Memoria | `AsyncPostgresSaver` sobre Supabase |
| Contenedores | Docker + Docker Compose |

## Estructura

```
app/
├── main.py               # App FastAPI, CORS y lifespan (abre/cierra la BD)
├── core/config.py        # Variables de entorno (pydantic-settings)
├── agent/
│   ├── state.py          # Estado del agente (lista de mensajes)
│   └── graph.py          # Grafo: un nodo "agent" que responde
├── agent/prompts.py      # System prompt del asistente
├── api/v1/router.py      # Endpoint de historial /api/v1/chat/...
├── bot/
│   ├── setup.py          # Crea la app de Telegram (si hay token)
│   └── handlers.py       # /start y mensajes → agente
├── db/checkpoint.py      # Pool de conexiones + checkpointer (memoria)
└── services/llm_factory.py  # Elige el LLM según LLM_PROVIDER
```

## Cómo funciona

```
Telegram ──mensaje──► bot (polling) ──► LangGraph (nodo agent + system prompt)
                                             │
                                             ▼
          Checkpointer ──► Supabase (historial por usuario: telegram-<user_id>)
```

1. **Al arrancar** (`lifespan`), se abre el pool de conexiones a Supabase, se crean las tablas de checkpoints si no existen y se inicia el bot de Telegram. Si la base de datos no responde, la API **no arranca**.
2. Cada mensaje de Telegram se envía al agente con `thread_id = telegram-<user_id>`, así el agente recuerda la conversación de cada usuario.
3. El agente responde según el system prompt (`app/agent/prompts.py`) y la respuesta se envía de vuelta al chat.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Estado del servicio |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/chat/sessions/{session_id}/history` | Historial de una sesión |

> Swagger UI disponible en `/docs` (schema en `/openapi.json`). ReDoc está desactivado.

### Ejemplo

```bash
curl http://localhost:8000/api/v1/chat/sessions/telegram-<user_id>/history
```

## Configuración (`.env`)

Crea un archivo `.env` en la raíz del proyecto:

```env
# Supabase — usar el Transaction pooler (IPv4), no la conexión directa
DATABASE_HOST="aws-0-<region>.pooler.supabase.com"
DATABASE_PORT=6543
DATABASE_USER="postgres.<project-ref>"
DATABASE_NAME="postgres"
DATABASE_PASSWORD=<password-de-la-base-de-datos>
DATABASE_URL="postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}?sslmode=require"

# LLM: ollama | gemini
LLM_PROVIDER=ollama

# Ollama (si LLM_PROVIDER=ollama): OLLAMA_MODEL obligatorio, no necesita token
OLLAMA_BASE_URL=http://localhost:11434   # en docker compose se usa http://ollama:11434
OLLAMA_MODEL=llama3.2:latest

# Telegram
TELEGRAM_BOT_TOKEN=<token-de-botfather>
TELEGRAM_ALLOWED_USER_IDS=<tu-id>   # separados por coma; vacío = cualquiera

# Gemini (si LLM_PROVIDER=gemini): GEMINI_MODEL y GEMINI_API_KEY obligatorios
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=
```

Según `LLM_PROVIDER`, la API valida al arrancar que estén las variables que ese proveedor necesita (el modelo y, en Gemini, `GEMINI_API_KEY`). Si falta alguna, no arranca y el error dice cuál.

**Notas sobre Supabase:**
- La conexión directa (`db.<ref>.supabase.co:5432`) solo funciona por IPv6, y Docker Desktop en Mac normalmente no lo soporta. Usa el **Transaction pooler** (puerto `6543`).
- En el pooler, el usuario debe incluir el ID del proyecto: `postgres.<project-ref>`.
- La contraseña es la **de la base de datos** (Project Settings → Database), no la de tu cuenta ni una API key.
- El `.env` **no se copia a la imagen** (está en `.dockerignore`). Docker Compose lo inyecta como variables de entorno con `env_file`.

## Levantar con Docker

```bash
# Construir y arrancar (API + Ollama)
docker compose up -d --build

# Descargar el modelo de Ollama (solo la primera vez)
docker exec ollama ollama pull llama3.2

# Ver logs
docker compose logs -f api

# Aplicar cambios del .env
docker compose up -d --force-recreate api

# Detener
docker compose down
```

| Servicio | Puerto |
|---|---|
| API | http://localhost:8000 |
| Ollama | http://localhost:11434 |

## Desarrollo local (sin Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Con `LLM_PROVIDER=ollama` necesitas Ollama corriendo localmente.
