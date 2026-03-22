# RAG Chatbot

A retrieval-augmented generation chatbot built with **FastAPI**, **PocketBase**, and **Caddy**. Supports switching between multiple Google Cloud retrieval backends or running as a direct Gemini chatbot with a configurable system prompt.

## Architecture

```
                   ┌──────────┐
  Browser ────────>│  Caddy   │  (auto-HTTPS, reverse proxy)
                   └────┬─────┘
                        │
              ┌─────────┴─────────┐
              v                   v
        ┌──────────┐       ┌───────────┐
        │ FastAPI  │<----->│PocketBase │
        │ :8000    │       │  :8090    │
        └────┬─────┘       └───────────┘
             │              Users, roles,
             │              RAG configs,
             │              chat history
             v
    ┌────────────────────┐
    │  Google Cloud       │
    │  ┌───────────────┐ │
    │  │ Gemini LLM    │ │
    │  └───────────────┘ │
    │  ┌───────────────┐ │
    │  │ RAG Store     │ │
    │  │ Vertex Search │ │
    │  │ Vector Search │ │
    │  └───────────────┘ │
    └────────────────────┘
```

## Retrieval Backends

| Backend | Value | Description |
|---|---|---|
| **None** | `none` | Direct Gemini chat — no retrieval. Uses the system prompt from PocketBase config. |
| **RAG Store** | `rag_store` | Vertex AI RAG Store (managed RAG corpus) |
| **Vertex Search** | `vertex_search` | Vertex AI Search (Discovery Engine) |
| **Vector Search** | `vector_search` | Vertex AI Vector Search (Matching Engine) |

Set the default in `.env` via `DEFAULT_RETRIEVAL_BACKEND`, or override per-request in the chat API.

## Two UIs

| URL | Who | Description |
|---|---|---|
| `/` | Regular users | Clean chat interface. No backend selectors, no sources, no admin controls. Branding (icon, name, welcome text) loaded from `.env`. |
| `/admin` | Superusers | Full admin chat with backend/config dropdowns, source citations, and access to stats API. |

Both UIs share the same auth system. The admin UI loads config selectors; the user UI just sends queries to the active config.

See [docs/user-ui.md](docs/user-ui.md) and [docs/admin-ui.md](docs/admin-ui.md) for detailed guides.

## Project Structure

```
├── .env.example              # Full env template (VM / production)
├── .env.local.example        # Minimal env template (localhost)
├── Caddyfile                 # Reverse proxy config
├── Dockerfile                # Python 3.12 FastAPI image
├── docker-compose.yml        # Production: Caddy + FastAPI + PocketBase
├── docker-compose.local.yml  # Local override: no Caddy, ports exposed
├── requirements.txt          # Python dependencies
├── app/
│   ├── main.py               # FastAPI entry point, serves UI at /
│   ├── config.py             # Pydantic settings loaded from .env
│   ├── auth.py               # PocketBase JWT auth middleware
│   ├── static/
│   │   ├── index.html        # Admin chat UI (/admin)
│   │   └── user.html         # Regular user chat UI (/)
│   ├── routers/
│   │   ├── auth_routes.py    # POST /api/auth/login, /api/auth/register
│   │   ├── chat.py           # POST /api/chat
│   │   └── admin.py          # CRUD /api/admin/rag-configs (superuser only)
│   ├── retrieval/
│   │   ├── base.py           # BaseRetriever ABC + RetrievalParams dataclass
│   │   ├── rag_store.py      # Vertex AI RAG Store retriever
│   │   ├── vertex_search.py  # Vertex AI Search retriever
│   │   └── vector_search.py  # Vertex AI Vector Search retriever
│   └── services/
│       ├── pocketbase.py     # PocketBase REST client
│       ├── chat.py           # Chat orchestration: config -> retrieve -> LLM
│       ├── stats.py          # Usage statistics from PocketBase
│       └── notifier.py       # Error email notifications to superusers
├── pb/
│   └── pb_migrations/
│       └── 1_create_collections.js   # Creates users role, rag_configs, chat_history
├── tests/
│   ├── conftest.py               # Shared fixtures (tokens, URLs)
│   ├── test_health.py            # Service health checks
│   ├── test_auth.py              # Auth flow tests
│   ├── test_rag_configs.py       # CRUD tests for all backend configs
│   ├── test_retrieval_params.py  # Unit tests for param merging logic
│   └── test_chat_integration.py  # Chat endpoint integration tests
├── docs/
│   ├── admin-ui.md           # Admin UI documentation
│   └── user-ui.md            # User UI documentation
└── scripts/
    ├── setup.sh              # One-command VM setup
    ├── run_local.sh          # Local dev runner (docker or bare-metal)
    └── deploy.sh             # Deploy to GCE instance
```

## Prerequisites

- **Docker** and **Docker Compose** (for containerized setup)
- **Python 3.10+** (for bare-metal local dev)
- A **Google Cloud** project with Vertex AI APIs enabled (required for Gemini and retrieval backends)
- A **GCP service account** JSON key with Vertex AI permissions

## Quick Start (Local Development)

### Option A: Docker (recommended)

```bash
git clone <repo-url> && cd chatbot

# Create .env from the local template
cp .env.local.example .env

# Edit .env — at minimum set:
#   GCP_PROJECT_ID=your-project-id
#   POCKETBASE_ADMIN_EMAIL=admin@example.com
#   POCKETBASE_ADMIN_PASSWORD=your-secure-password

# Start FastAPI + PocketBase (no Caddy)
bash scripts/run_local.sh docker
```

Services will be available at:

| Service | URL |
|---|---|
| Chat UI | http://localhost:8000 |
| FastAPI Swagger docs | http://localhost:8000/api/docs |
| PocketBase Admin | http://localhost:8090/_/ |

### Option B: Bare-metal (no Docker)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Download PocketBase (https://pocketbase.io/docs/)
# Place the binary in your PATH or in ./pb/

cp .env.local.example .env
# Edit .env — set POCKETBASE_URL=http://localhost:8090

bash scripts/run_local.sh bare
```

This starts PocketBase on `:8090` and FastAPI with hot-reload on `:8000`.

## Production Setup (GCE VM)

### 1. SSH into your VM and clone the repo

```bash
git clone <repo-url> && cd chatbot
```

### 2. Run the setup script

```bash
bash scripts/setup.sh
```

This will:
- Copy `.env.example` to `.env` (if not present)
- Install Docker if missing
- Start Caddy + FastAPI + PocketBase via Docker Compose

### 3. Configure environment

```bash
# Edit .env with your real values
nano .env
```

Required variables:

| Variable | Description |
|---|---|
| `GCP_PROJECT_ID` | Your Google Cloud project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON inside the container (`/app/credentials/service-account.json`) |
| `POCKETBASE_ADMIN_EMAIL` | PocketBase superuser email |
| `POCKETBASE_ADMIN_PASSWORD` | PocketBase superuser password |
| `DOMAIN` | Your domain for Caddy HTTPS (e.g. `chat.example.com`) |

### 4. Add GCP credentials

```bash
mkdir -p credentials
# Copy your service account key
cp /path/to/service-account.json credentials/service-account.json
```

### 5. Restart

```bash
docker compose up -d --build
```

### 6. Create the PocketBase admin account

Open `http://YOUR_DOMAIN/pb/_/` and create the first admin account, or run:

```bash
docker compose exec pocketbase ./pocketbase superuser upsert admin@example.com your-password
```

## Remote Deploy

Deploy from your local machine to a GCE instance:

```bash
# Syncs code and runs setup.sh on the remote VM
bash scripts/deploy.sh my-instance-name us-central1-a
```

The script uses `gcloud compute scp` and `gcloud compute ssh`. It excludes `.env`, `credentials/`, and `pb/pb_data/` from the sync — you must configure those on the VM.

## Initial Configuration

### 1. Create a user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password", "name": "Your Name"}'
```

### 2. Promote user to superuser (via PocketBase admin)

Open PocketBase admin UI (`http://localhost:8090/_/`), navigate to the **users** collection, find the user, and set their `role` field to `superuser`.

### 3. Log in

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

Save the `token` from the response.

### 4. Create a RAG config

```bash
curl -X POST http://localhost:8000/api/admin/rag-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Default",
    "retrieval_backend": "none",
    "llm_model": "gemini-2.0-flash",
    "temperature": 0.3,
    "top_k": 5,
    "max_output_tokens": 2048,
    "system_prompt": "You are a helpful assistant. Answer questions clearly and concisely.",
    "is_active": true
  }'
```

### 5. Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "Hello, how are you?"}'
```

Or just open http://localhost:8000 in your browser and use the web UI.

## Changing Configuration

All retrieval and LLM parameters are managed through PocketBase `rag_configs` records. You can change them in three ways:

### Via the Admin API

```bash
# Update an existing config
curl -X PATCH http://localhost:8000/api/admin/rag-configs/CONFIG_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"temperature": 0.7, "system_prompt": "New prompt here"}'
```

### Via PocketBase Admin UI

1. Open http://localhost:8090/_/
2. Navigate to the **rag_configs** collection
3. Edit any record directly in the UI
4. Changes take effect immediately on the next chat request

### Via the Chat Web UI

The settings bar at the top of the chat UI lets you select:
- **Backend**: override the retrieval backend per-request
- **Config ID**: pick a specific config from the dropdown

## RAG Config Parameters Reference

Each `rag_configs` record in PocketBase contains these fields:

### General

| Field | Type | Description |
|---|---|---|
| `name` | text | Display name for this configuration |
| `description` | text | Optional description |
| `retrieval_backend` | select | `none`, `rag_store`, `vertex_search`, or `vector_search` |
| `is_active` | bool | If `true`, this config is used as the default when no `config_id` is specified |

### LLM Settings

| Field | Type | Default | Description |
|---|---|---|---|
| `llm_model` | text | `gemini-2.0-flash` | Gemini model name |
| `temperature` | number | `0.3` | Generation temperature (0-2). Lower = more deterministic |
| `top_k` | number | `5` | Number of retrieval results to fetch |
| `max_output_tokens` | number | `2048` | Maximum tokens in the LLM response (1-65536) |
| `system_prompt` | text | | System instruction sent to Gemini. Used in both direct and RAG modes |
| `top_p` | number | | Nucleus sampling parameter (0-1). Alternative to temperature |

### RAG Store Parameters

Used when `retrieval_backend` = `rag_store`.

| Field | Type | Description |
|---|---|---|
| `rag_corpus_name` | text | Full resource name: `projects/{p}/locations/{l}/ragCorpora/{id}` |
| `rag_similarity_top_k` | number | Override for similarity search top-k (defaults to `top_k`) |
| `rag_vector_distance_threshold` | number | Minimum similarity score (0-1). Chunks below this are filtered out |

### Vertex AI Search Parameters

Used when `retrieval_backend` = `vertex_search`.

| Field | Type | Description |
|---|---|---|
| `vs_serving_config` | text | Full serving config resource name |
| `vs_datastore` | text | Full datastore resource name |
| `vs_filter` | text | Filter expression (e.g. `category: ANY("docs")`) |
| `vs_order_by` | text | Sort order (e.g. `relevance_score desc`) |
| `vs_boost_spec` | json | Boost specification for result ranking. Format: `{"condition_boost_specs": [{"condition": "...", "boost": 0.5}]}` |
| `vs_query_expansion` | bool | Enable automatic query expansion |
| `vs_spell_correction` | bool | Enable automatic spell correction |
| `vs_summary_result_count` | number | Number of results to include in summary (0 = no summary) |
| `vs_snippet_result_count` | number | Max snippets per result (0 = no snippets) |

### Vector Search (Matching Engine) Parameters

Used when `retrieval_backend` = `vector_search`.

| Field | Type | Description |
|---|---|---|
| `vec_index_endpoint` | text | Full index endpoint resource name |
| `vec_deployed_index_id` | text | ID of the deployed index |
| `vec_embedding_model` | text | Embedding model name (default: `text-embedding-005`) |
| `vec_approx_neighbor_count` | number | Approximate neighbor count for ANN search (1-1000) |
| `vec_fraction_leaf_nodes` | number | Fraction of leaf nodes to search (0-1). Higher = more accurate but slower |
| `vec_filter_restricts` | json | Namespace filter restricts. Format: `[{"namespace": "color", "allow": ["red"], "deny": ["blue"]}]` |
| `vec_return_full_datapoint` | bool | Return full datapoint data with results |

### Example Configs

**Direct Gemini (no retrieval):**
```json
{
  "name": "Customer Support Bot",
  "retrieval_backend": "none",
  "llm_model": "gemini-2.0-flash",
  "temperature": 0.3,
  "max_output_tokens": 2048,
  "system_prompt": "You are a customer support agent for Acme Corp...",
  "is_active": true
}
```

**RAG Store:**
```json
{
  "name": "Internal Docs Search",
  "retrieval_backend": "rag_store",
  "rag_corpus_name": "projects/my-project/locations/us-central1/ragCorpora/abc123",
  "rag_similarity_top_k": 10,
  "rag_vector_distance_threshold": 0.6,
  "system_prompt": "Answer using the provided documentation context.",
  "is_active": false
}
```

**Vertex AI Search:**
```json
{
  "name": "Website Search",
  "retrieval_backend": "vertex_search",
  "vs_serving_config": "projects/my-project/locations/global/collections/default_collection/dataStores/my-ds/servingConfigs/default_serving_config",
  "vs_datastore": "projects/my-project/locations/global/collections/default_collection/dataStores/my-ds",
  "vs_query_expansion": true,
  "vs_spell_correction": true,
  "vs_summary_result_count": 3,
  "vs_filter": "category: ANY(\"help-articles\")",
  "is_active": false
}
```

**Vector Search:**
```json
{
  "name": "Product Embeddings",
  "retrieval_backend": "vector_search",
  "vec_index_endpoint": "projects/my-project/locations/us-central1/indexEndpoints/ep1",
  "vec_deployed_index_id": "products_v2",
  "vec_embedding_model": "text-embedding-005",
  "vec_approx_neighbor_count": 100,
  "vec_fraction_leaf_nodes": 0.1,
  "vec_filter_restricts": [{"namespace": "department", "allow": ["electronics"], "deny": []}],
  "vec_return_full_datapoint": true,
  "is_active": false
}
```

## API Endpoints

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create a new user |
| POST | `/api/auth/login` | Log in, returns JWT token |

### Chat

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/chat` | User | Send a query. Optionally pass `backend`, `config_id`, `top_k`. |

**Request body:**

```json
{
  "query": "What is RAG?",
  "backend": "none",
  "config_id": "optional-pocketbase-record-id",
  "top_k": 5
}
```

- `backend` — Override the retrieval backend for this request. Omit to use the active PocketBase config or `.env` default.
- `config_id` — Use a specific PocketBase `rag_configs` record. Omit to use the one with `is_active=true`.
- `top_k` — Number of retrieval results (ignored when backend is `none`).

### Admin (superuser only)

| Method | Path | Description |
|---|---|---|
| GET | `/api/admin/rag-configs` | List all RAG configs |
| GET | `/api/admin/rag-configs/{id}` | Get a specific config |
| POST | `/api/admin/rag-configs` | Create a config |
| PATCH | `/api/admin/rag-configs/{id}` | Update a config |
| DELETE | `/api/admin/rag-configs/{id}` | Delete a config |
| GET | `/api/admin/stats` | Usage statistics (users, chats, backends) |

### Utility

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/branding` | Public branding info (name, icon, welcome text) |
| GET | `/api/docs` | Swagger UI |
| GET | `/` | Regular user chat UI |
| GET | `/admin` | Admin chat UI (backend/config selectors) |

## PocketBase Collections

The migration at `pb/pb_migrations/1_create_collections.js` creates:

**users** (extended built-in):
- `role` — `select`: `user` or `superuser`

**rag_configs** — 29 fields covering all backends. See [RAG Config Parameters Reference](#rag-config-parameters-reference) above.

**chat_history**:
- `user` — Relation to users collection
- `query` — User's question
- `answer` — LLM response
- `backend` — Which backend was used
- `sources` — JSON array of retrieval sources
- `config_id` — Which rag_config was used

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `GCP_PROJECT_ID` | _(empty)_ | Google Cloud project ID |
| `GCP_LOCATION` | `us-central1` | GCP region |
| `GOOGLE_APPLICATION_CREDENTIALS` | _(empty)_ | Path to service account JSON |
| `DEFAULT_RETRIEVAL_BACKEND` | `none` | Default backend: `none`, `rag_store`, `vertex_search`, `vector_search` |
| `RAG_CORPUS_NAME` | _(empty)_ | Full resource name of the RAG corpus |
| `VERTEX_SEARCH_DATASTORE` | _(empty)_ | Full resource name of the Vertex Search datastore |
| `VERTEX_SEARCH_SERVING_CONFIG` | _(empty)_ | Full resource name of the serving config |
| `VECTOR_SEARCH_INDEX_ENDPOINT` | _(empty)_ | Full resource name of the Vector Search index endpoint |
| `VECTOR_SEARCH_DEPLOYED_INDEX_ID` | _(empty)_ | Deployed index ID |
| `EMBEDDING_MODEL` | `text-embedding-005` | Embedding model for Vector Search |
| `LLM_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `LLM_TEMPERATURE` | `0.3` | Generation temperature |
| `LLM_MAX_OUTPUT_TOKENS` | `2048` | Max output tokens |
| `POCKETBASE_URL` | `http://pocketbase:8090` | PocketBase URL (use `http://localhost:8090` for local dev) |
| `POCKETBASE_ADMIN_EMAIL` | _(empty)_ | PocketBase superuser email |
| `POCKETBASE_ADMIN_PASSWORD` | _(empty)_ | PocketBase superuser password |
| `API_HOST` | `0.0.0.0` | FastAPI bind host |
| `API_PORT` | `8000` | FastAPI bind port |
| `API_WORKERS` | `2` | Uvicorn workers |
| `LOG_LEVEL` | `info` | Log level |
| `DOMAIN` | `localhost` | Domain for Caddy (set to your real domain for auto-HTTPS) |
| `BOT_NAME` | `Chat Assistant` | Bot display name (title, headings) |
| `BOT_ICON_URL` | _(empty)_ | URL to bot icon (PNG/SVG, used as favicon too) |
| `WELCOME_TITLE` | `How can I help you?` | Welcome screen heading |
| `WELCOME_SUBTITLE` | `Ask me anything.` | Welcome screen subtext |
| `POWERED_BY_TEXT` | _(empty)_ | Footer text in user UI |
| `SMTP_HOST` | _(empty)_ | SMTP server for error emails (leave blank to disable) |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | _(empty)_ | SMTP login username |
| `SMTP_PASSWORD` | _(empty)_ | SMTP login password |
| `SMTP_FROM` | _(empty)_ | Sender email address |
| `SMTP_TLS` | `true` | Use STARTTLS |
| `ERROR_NOTIFY_EMAILS` | _(empty)_ | Comma-separated emails to receive error notifications |

`.env` values are used as fallback defaults. PocketBase config values override them per-config.

## Branding (Custom Icons and Text per Clone)

Each deployment can have its own identity. Set these in `.env`:

```env
BOT_NAME=Acme Support
BOT_ICON_URL=https://example.com/logo.png
WELCOME_TITLE=Welcome to Acme Support
WELCOME_SUBTITLE=Ask about our products, billing, or anything else.
POWERED_BY_TEXT=Powered by Acme AI
```

| Variable | What it controls |
|---|---|
| `BOT_NAME` | Page title, login heading, top bar name |
| `BOT_ICON_URL` | Icon on login screen, welcome area, top bar, and browser favicon |
| `WELCOME_TITLE` | Large heading on the welcome screen (before first message) |
| `WELCOME_SUBTITLE` | Smaller text below the welcome heading |
| `POWERED_BY_TEXT` | Footer text at the bottom of the user chat UI |

These values are served via `GET /api/branding` (public, no auth) so the UIs load them dynamically. Change `.env` and restart to rebrand.

## Statistics

Superusers can retrieve usage stats via:

```bash
curl http://localhost:8000/api/admin/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Returns:

```json
{
  "users": { "total": 42, "superusers": 3, "regular": 39 },
  "chats": {
    "total": 1280,
    "by_backend": { "none": 800, "rag_store": 300, "vertex_search": 150, "vector_search": 30 }
  },
  "recent_chats": [ ... last 10 queries ... ],
  "configs": { "total": 4, "active": { "id": "...", "name": "Default", "retrieval_backend": "none" } }
}
```

## Error Email Notifications

Configure SMTP in `.env` to send error emails to chosen superusers:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=alerts@example.com
SMTP_TLS=true
ERROR_NOTIFY_EMAILS=admin1@example.com,admin2@example.com
```

When an unhandled error occurs in any API endpoint, the configured superusers receive an HTML email containing:
- Error type and message
- Which endpoint was called
- Which user triggered it
- Full Python traceback
- Timestamp and domain

Leave `SMTP_HOST` empty to disable email notifications.

## Switching Between Backends

You can switch retrieval backends in three ways:

1. **`.env` default** — Set `DEFAULT_RETRIEVAL_BACKEND` for the whole instance.
2. **PocketBase config** — Create a `rag_configs` record with `is_active=true`. Its `retrieval_backend` overrides the `.env` default.
3. **Per-request** — Pass `"backend": "vertex_search"` in the chat request body to override for a single query.

Priority: **per-request > PocketBase config > .env default**.

## Running Tests

Tests require both PocketBase (`:8090`) and FastAPI (`:8000`) running locally.

```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
python -m pytest tests/ -v
```

### Test suites

| File | What it tests |
|---|---|
| `test_health.py` | FastAPI and PocketBase health, UI serving |
| `test_auth.py` | Login, register, token validation |
| `test_rag_configs.py` | Full CRUD for all 4 backend types with all parameters |
| `test_retrieval_params.py` | Unit tests for `RetrievalParams` merging (PB config over .env) |
| `test_chat_integration.py` | Config round-trips, active config selection, input validation |

## Running on Multiple VMs

1. Clone the repo on each VM
2. Run `bash scripts/setup.sh`
3. Edit `.env` on each VM with the shared GCP project but potentially different settings (region, backend, etc.)
4. Each VM gets its own PocketBase instance with independent users and configs
5. Set `DOMAIN` to the VM's public hostname for Caddy to auto-provision HTTPS via Let's Encrypt
