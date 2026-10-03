# nexus-agents

API de agentes de IA construida con **FastAPI** y **LangGraph**. El agente responde en tiempo real por **SSE** (Server-Sent Events), puede ejecutar herramientas (tools) y recuerda cada conversación guardándola en **Supabase (PostgreSQL)**.

## Stack

| Pieza | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Agente | LangGraph (`StateGraph` + `ToolNode`) |
| LLM | Ollama (local), Google Gemini o AWS Bedrock — configurable |
| Memoria | `AsyncPostgresSaver` sobre Supabase |
| Contenedores | Docker + Docker Compose |

## Estructura

```
app/
├── main.py               # App FastAPI, CORS y lifespan (abre/cierra la BD)
├── core/config.py        # Variables de entorno (pydantic-settings)
├── agent/
│   ├── state.py          # Estado del agente (lista de mensajes)
│   └── graph.py          # Grafo: nodo "agent" ⇄ nodo "tools"
├── api/v1/
│   ├── router.py         # Endpoints /api/v1/chat/...
│   └── sse.py            # Convierte los eventos del agente a SSE
├── db/checkpoint.py      # Pool de conexiones + checkpointer (memoria)
└── services/llm_factory.py  # Elige el LLM según LLM_PROVIDER
```

## Cómo funciona

```
Cliente ──POST /chat/stream──► FastAPI ──► LangGraph
                                             │
                     ┌───────────────────────┤
                     ▼                       ▼
                 nodo agent  ◄──────►   nodo tools
                 (LLM decide)          (ejecuta la tool)
                     │
                     ▼
          Checkpointer ──► Supabase (guarda el historial por session_id)
```

1. **Al arrancar** (`lifespan`), se abre el pool de conexiones a Supabase y se crean las tablas de checkpoints si no existen. Si la base de datos no responde, la API **no arranca**.
2. Cada petición trae un `session_id`. El checkpointer carga el historial de esa sesión, así que el agente recuerda lo anterior.
3. El LLM responde o pide ejecutar una tool. Si pide una tool, se ejecuta y el resultado vuelve al LLM.
4. Los tokens y eventos se envían al cliente a medida que se generan.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Estado del servicio |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/chat/stream` | Envía un mensaje al agente (respuesta SSE) |
| `GET` | `/api/v1/chat/sessions/{session_id}/history` | Historial de una sesión |

> Swagger (`/docs`), ReDoc y `/openapi.json` están desactivados en `main.py`.

### Ejemplo

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "¿Cuál es el estado del servicio auth?", "session_id": "demo-1"}'
```

Eventos SSE que puede devolver:

| `type` | Significado |
|---|---|
| `token` | Trozo de texto generado por el LLM |
| `tool_start` | El agente invocó una herramienta |
| `tool_end` | Resultado de la herramienta |
| `error` | Ocurrió un error |
| `done` | Fin del turno |

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

# LLM: ollama | gemini | bedrock
LLM_PROVIDER=ollama

# Gemini (si LLM_PROVIDER=gemini)
GEMINI_API_KEY=

# Bedrock (si LLM_PROVIDER=bedrock)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
BEDROCK_MODEL_ID=
```

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

## Agregar herramientas

Las tools se definen en `app/agent/graph.py` con el decorador `@tool` y se añaden a la lista `tools`:

```python
@tool
def get_system_status(service_name: str) -> str:
    """Consulta el estado operativo de un servicio."""
    return f"Servicio '{service_name}': OPERATIVO"

tools = [get_system_status]
```

El docstring es importante: es lo que lee el LLM para decidir cuándo usar la herramienta.
