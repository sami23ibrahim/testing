# RAG Chatbot - Extended Documentation

This document is the comprehensive technical reference for the RAG Chatbot project. It covers every component, configuration option, deployment scenario, and operational procedure in detail.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Architecture Deep Dive](#3-architecture-deep-dive)
4. [Component Breakdown](#4-component-breakdown)
5. [Retrieval Backends In-Depth](#5-retrieval-backends-in-depth)
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [Authentication & Authorization](#8-authentication--authorization)
9. [Branding & Customization](#9-branding--customization)
10. [Error Handling & Notifications](#10-error-handling--notifications)
11. [Statistics & Monitoring](#11-statistics--monitoring)
12. [Prerequisites](#12-prerequisites)
13. [Installation & Setup](#13-installation--setup)
14. [Cloning for Multiple Deployments](#14-cloning-for-multiple-deployments)
15. [Testing](#15-testing)
16. [Environment Variables Reference](#16-environment-variables-reference)
17. [Troubleshooting](#17-troubleshooting)
18. [Security Considerations](#18-security-considerations)

---

## 1. Project Overview

### What the Project Is

The RAG Chatbot is a production-ready, retrieval-augmented generation chatbot built on FastAPI, PocketBase, and Caddy. It provides a web-based conversational interface backed by Google Gemini large language models, with optional retrieval from Google Cloud data stores to ground LLM responses in domain-specific content.

### What Problem It Solves

Organizations need to deploy internal or customer-facing chatbots that can answer questions using their own data, not just the LLM's training knowledge. This project solves that by providing:

- A complete, self-contained chatbot stack that can be deployed on a single VM.
- Pluggable retrieval backends so the same codebase can work with different Google Cloud data services depending on what the organization has set up.
- A configuration layer (PocketBase) that lets administrators change the system prompt, retrieval backend, LLM model, and all tuning parameters at runtime -- without code changes or redeployments.
- Two separate UIs: a clean user-facing chat and a full-featured admin chat with backend selectors and source citations.
- Support for cloning the project to run multiple independent chatbot instances with different branding, data sources, and configurations.

### Key Features Summary

- **Four retrieval modes**: No retrieval (direct Gemini), RAG Store, Vertex AI Search, and Vector Search.
- **Runtime configuration**: All LLM and retrieval parameters are stored in PocketBase and can be changed without restarting the server.
- **Two web interfaces**: A simplified user UI at `/` and a full admin UI at `/admin`.
- **Role-based access**: PocketBase JWT authentication with `user` and `superuser` roles.
- **Per-clone branding**: Bot name, icon, welcome text, and footer are configurable per deployment via environment variables.
- **Error email notifications**: SMTP-based alerts to superusers when unhandled errors occur.
- **Usage statistics**: API endpoint for superusers to monitor user counts, chat volumes, and backend usage.
- **Auto-HTTPS**: Caddy reverse proxy handles TLS certificate provisioning via Let's Encrypt.
- **One-command deployment**: Scripts for VM setup, local development, and remote deploy via `gcloud`.
- **Comprehensive test suite**: Health checks, auth flow tests, CRUD tests for all backend configs, parameter merging unit tests, and chat integration tests.

---

## 2. Technology Stack

### FastAPI

**What it is**: FastAPI is a modern, high-performance Python web framework for building APIs. It is built on top of Starlette for the ASGI layer and Pydantic for data validation.

**Why it was chosen**: FastAPI provides automatic request/response validation via Pydantic models, built-in Swagger documentation at `/api/docs`, native async/await support for non-blocking I/O (important when calling PocketBase and Google Cloud APIs), and excellent performance characteristics for a Python framework. Its type-hint-driven design reduces boilerplate and catches errors at development time.

### PocketBase

**What it is**: PocketBase is a lightweight, open-source backend-as-a-service that provides a SQLite-based database, a REST API, real-time subscriptions, authentication, and an admin dashboard -- all in a single binary.

**Why it was chosen**: PocketBase eliminates the need for a separate database server, ORM layer, and user management system. It provides a built-in admin UI for data management, a migration system for schema changes, JWT-based authentication out of the box, and collection-level access rules. Running as a single Go binary, it has minimal resource requirements and is well-suited for VM deployments. Its REST API is consumed directly by the FastAPI backend via httpx.

### Caddy

**What it is**: Caddy is a web server and reverse proxy that automatically obtains and renews TLS certificates from Let's Encrypt.

**Why it was chosen**: Caddy provides automatic HTTPS with zero configuration beyond specifying the domain name. It handles certificate provisioning, renewal, OCSP stapling, and HTTP-to-HTTPS redirection automatically. In this project it acts as the single entry point, routing `/api/*` to FastAPI, `/pb/*` and `/_/*` to PocketBase, and serving the chat UIs. This eliminates the need for manual certificate management with tools like certbot.

### Docker and Docker Compose

**What it is**: Docker is a container runtime. Docker Compose is a tool for defining and running multi-container applications.

**Why it was chosen**: The project runs three services (Caddy, FastAPI, PocketBase) that need to communicate on an internal network. Docker Compose defines the entire stack in a single `docker-compose.yml` file, handles service dependencies, volume management, and networking. It ensures consistent environments across development and production. The local override file (`docker-compose.local.yml`) disables Caddy and exposes ports directly for development.

### Google Cloud Vertex AI / Gemini

**What it is**: Vertex AI is Google Cloud's machine learning platform. Gemini is Google's family of large language models available through Vertex AI. The project uses several Vertex AI services:

- **Gemini LLM**: The core language model that generates chat responses. Used in all four retrieval modes.
- **RAG Store**: A managed RAG corpus service where you upload documents and Google handles chunking, embedding, and retrieval.
- **Vertex AI Search (Discovery Engine)**: A managed search service that supports structured and unstructured data, with built-in query expansion, spell correction, and summarization.
- **Vector Search (Matching Engine)**: A high-performance approximate nearest neighbor search service for custom embeddings.

**Why it was chosen**: The Gemini model family provides strong performance across a range of tasks. Vertex AI offers multiple retrieval services at different levels of abstraction, allowing teams to choose the one that fits their data and requirements. All services are authenticated via a single GCP service account.

### Python Libraries

| Library | Version | Purpose |
|---|---|---|
| `fastapi` | 0.115.12 | Web framework for the REST API. Provides routing, dependency injection, middleware, and automatic OpenAPI documentation. |
| `uvicorn[standard]` | 0.34.2 | ASGI server that runs the FastAPI application. The `[standard]` extras include uvloop and httptools for better performance. The `--reload` flag enables hot-reloading during development. |
| `pydantic` | 2.11.1 | Data validation library used for request/response models (`ChatRequest`, `LoginRequest`, `RAGConfigPayload`) and the `RetrievalBackend` enum. |
| `pydantic-settings` | 2.9.1 | Extension of Pydantic for loading settings from environment variables and `.env` files. Powers the `Settings` class in `app/config.py`. |
| `httpx` | 0.28.1 | Async HTTP client used by the PocketBase client (`app/services/pocketbase.py`) and the stats service to make REST API calls to PocketBase. Also used in the test suite. |
| `google-cloud-aiplatform` | 1.88.0 | Google Cloud SDK for Vertex AI. Provides the `vertexai` module for Gemini model calls, the `rag` preview API for RAG Store retrieval, and the `MatchingEngineIndexEndpoint` class for Vector Search. |
| `google-cloud-discoveryengine` | 0.13.7 | Google Cloud SDK for the Discovery Engine API (Vertex AI Search). Provides the `SearchServiceClient` and request/response types for search queries. |
| `google-auth` | 2.40.1 | Google authentication library. Handles service account credential loading from the JSON key file specified by `GOOGLE_APPLICATION_CREDENTIALS`. |
| `python-dotenv` | 1.1.0 | Loads environment variables from `.env` files. Used by pydantic-settings to populate the `Settings` class. |

---

## 3. Architecture Deep Dive

### Overall System Architecture

```
                         Internet
                            |
                            v
                    +---------------+
                    |    Caddy      |  Port 80/443
                    |  (auto-HTTPS) |
                    +-------+-------+
                            |
              +-------------+-------------+
              |                           |
     /api/* routes               /pb/*, /_/* routes
              |                           |
              v                           v
     +----------------+          +----------------+
     |    FastAPI      |  <-----> |   PocketBase   |
     |    :8000        |  httpx   |    :8090       |
     +--------+-------+          +----------------+
              |                    - users collection
              |                    - rag_configs collection
              |                    - chat_history collection
              v                    - JWT auth
     +-------------------+
     |   Google Cloud     |
     |                    |
     |  +- Gemini LLM    |
     |  +- RAG Store     |
     |  +- Vertex Search |
     |  +- Vector Search |
     +-------------------+
```

In production, all three services run as Docker containers on the same host, connected via a Docker network. Caddy is the only container that exposes ports to the outside world (80 and 443). FastAPI and PocketBase communicate over the internal Docker network using their service names as hostnames.

In local development, Caddy is disabled. FastAPI is exposed directly on port 8000 and PocketBase on port 8090.

### Request Flow: How a Chat Message Travels

Here is the complete lifecycle of a chat message, from the moment the user presses Enter to the moment the response appears in the browser:

```
Browser                  Caddy             FastAPI              PocketBase          Google Cloud
  |                        |                  |                     |                    |
  |-- POST /api/chat ----->|                  |                     |                    |
  |                        |-- proxy -------->|                     |                    |
  |                        |                  |                     |                    |
  |                        |                  |-- verify JWT ------>|                    |
  |                        |                  |<-- user record -----|                    |
  |                        |                  |                     |                    |
  |                        |                  |-- get active ------>|                    |
  |                        |                  |   rag_config        |                    |
  |                        |                  |<-- config data -----|                    |
  |                        |                  |                     |                    |
  |                        |                  |   [if RAG mode]     |                    |
  |                        |                  |-- retrieve ---------|------------>       |
  |                        |                  |   chunks            |  RAG Store /       |
  |                        |                  |<--------------------|  Vertex Search /   |
  |                        |                  |                     |  Vector Search     |
  |                        |                  |                     |                    |
  |                        |                  |-- generate ---------|------------>       |
  |                        |                  |   (Gemini)          |   Gemini LLM      |
  |                        |                  |<--------------------|------------>       |
  |                        |                  |                     |                    |
  |                        |<-- JSON ---------|                     |                    |
  |<-- response -----------|                  |                     |                    |
```

**Step-by-step breakdown:**

1. **Browser sends request**: The user types a message. The JavaScript UI sends a `POST /api/chat` with the query, an optional `backend` override, an optional `config_id`, and `top_k`. The request includes a `Bearer` token in the `Authorization` header.

2. **Caddy proxies**: In production, Caddy receives the request on port 443 (HTTPS), terminates TLS, and proxies to `fastapi:8000` on the internal Docker network.

3. **FastAPI receives and authenticates**: The `chat` router function has a dependency on `get_current_user`, which extracts the JWT from the `Authorization` header and calls PocketBase's `auth-refresh` endpoint to validate it. If the token is invalid or expired, the request is rejected with a 401.

4. **Config resolution**: The `ask()` function in `app/services/chat.py` resolves the configuration. If a `config_id` was provided, it fetches that specific config from PocketBase. Otherwise, it looks for the config with `is_active=true`. The config provides the system prompt, LLM model, temperature, retrieval backend, and all backend-specific parameters.

5. **Parameter merging**: The `RetrievalParams.from_pb_config()` method merges PocketBase config values over `.env` defaults. For example, if the PB config has a `rag_corpus_name`, that is used. If the field is empty, the `.env` value (`RAG_CORPUS_NAME`) is used as a fallback. Per-request overrides (like `backend` and `top_k` in the chat request body) take highest priority.

6. **Retrieval (if not "none" mode)**: If the resolved backend is `rag_store`, `vertex_search`, or `vector_search`, the corresponding retriever is invoked. Each retriever calls a different Google Cloud API and returns a list of `RetrievedChunk` objects containing text, a relevance score, a source identifier, and metadata.

7. **Prompt construction**: For RAG modes, the `_build_rag_prompt()` function assembles a prompt that includes the system prompt, the retrieved context chunks (with source and score annotations), and the user's question. For "none" mode, the system prompt is passed as the model's `system_instruction` and the query is sent directly.

8. **LLM generation**: The Gemini model generates a response using the assembled prompt and the generation config (temperature, max_output_tokens, top_p).

9. **Response**: The response JSON contains the `answer` text, the `backend` that was used, the `config_id`, a `sources` array (empty for "none" mode, populated for RAG modes with truncated text, source URI, and score), and the `user` email.

### How the Retrieval Pipeline Works for Each Backend

**None (Direct Gemini)**: No retrieval step. The system prompt is set as the model's `system_instruction`. The user query is sent directly to `model.generate_content()`. The response is returned as-is.

**RAG Store**: The retriever calls `rag_api.retrieval_query()` from the `vertexai.preview.rag` module. It passes the corpus resource name, the query text, and the similarity top-k. Google's managed service handles embedding the query, searching the corpus, and returning ranked text chunks with scores and source URIs.

**Vertex AI Search**: The retriever instantiates a `SearchServiceClient` and builds a `SearchRequest` with the serving config, query, page size, and optional parameters (filter, order_by, boost_spec, query_expansion, spell_correction, summary_spec, snippet_spec). The Discovery Engine API returns search results with structured data, snippets, and relevance scores.

**Vector Search**: The retriever first embeds the query using the `TextEmbeddingModel` (default: `text-embedding-005`). It then calls `index_endpoint.find_neighbors()` with the embedding vector, the deployed index ID, the number of neighbors, and optional parameters (approximate neighbor count, fraction of leaf nodes, filter restricts). The Matching Engine returns neighbor IDs and distances. Note that Vector Search returns IDs, not text -- the actual text content lookup is application-specific and would need to be added based on how the data was indexed.

### Config Resolution Priority

The system uses a three-tier priority system for configuration:

```
Priority (highest to lowest):

1. Per-request parameters (in the POST /api/chat body)
   - backend: overrides retrieval_backend from config and .env
   - top_k: overrides top_k from config (only if different from default 5)
   - config_id: selects a specific config instead of the active one

2. PocketBase rag_config record
   - retrieval_backend, llm_model, temperature, top_k, max_output_tokens, top_p
   - system_prompt
   - All backend-specific params (rag_*, vs_*, vec_*)
   - If a field is empty/null in PB, falls back to .env

3. .env defaults
   - DEFAULT_RETRIEVAL_BACKEND
   - LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_OUTPUT_TOKENS
   - RAG_CORPUS_NAME, VERTEX_SEARCH_*, VECTOR_SEARCH_*, EMBEDDING_MODEL
```

This design means you can set base defaults in `.env`, override them per-config in PocketBase (e.g., different system prompts for different use cases), and still override per-request from the admin UI for testing.

---

## 4. Component Breakdown

### `app/main.py` -- Application Entry Point

This is the FastAPI application factory. It performs the following:

- **Creates the FastAPI app** with the title "RAG Chatbot", version "1.0.0", and Swagger docs at `/api/docs`.
- **Adds CORS middleware** allowing all origins, methods, and headers. This is necessary because the static HTML UIs are served from the same origin but may also be loaded from other contexts during development.
- **Includes routers** for auth (`/api/auth/*`), chat (`/api/chat`), and admin (`/api/admin/*`).
- **Defines the error notification middleware**: A middleware function wraps every request in a try/except. If an unhandled exception occurs, it logs the error, attempts to send an email notification via the notifier service, and returns a generic 500 JSON response. The user's email is extracted from `request.state.user` if available.
- **Defines the `/api/branding` endpoint**: A public (no auth) endpoint that returns the bot name, icon URL, welcome title, welcome subtitle, and powered-by text from the settings. Both UIs call this on load to display branding.
- **Defines the `/api/health` endpoint**: Returns `{"status": "ok"}` for health checks.
- **Mounts static files** from `app/static/` at `/static`.
- **Defines UI routes**: `GET /` serves `user.html` and `GET /admin` serves `index.html`.

### `app/config.py` -- Settings Management

This module defines the application configuration using pydantic-settings:

- **`RetrievalBackend` enum**: A string enum with four values: `none`, `rag_store`, `vertex_search`, `vector_search`. Used throughout the codebase for type-safe backend selection.
- **`Settings` class**: A `BaseSettings` subclass that loads values from environment variables and `.env` files. Every configurable parameter in the system has a corresponding field here with a sensible default. The `model_config` dict tells pydantic-settings to read from a `.env` file with UTF-8 encoding.
- **`settings` singleton**: A module-level instance of `Settings` that is imported by other modules. Created once at import time.

### `app/auth.py` -- Authentication

This module provides two FastAPI dependency functions:

- **`get_current_user()`**: Extracts the JWT from the `Authorization: Bearer <token>` header using FastAPI's `HTTPBearer` security scheme. Calls `pb.verify_user_token()` to validate the token against PocketBase. Returns the user record dict on success, raises HTTP 401 on failure.
- **`require_superuser()`**: Depends on `get_current_user()`, then checks that the user's `role` field is `"superuser"`. Raises HTTP 403 if not. Used by admin endpoints.

### `app/routers/auth_routes.py` -- Authentication Routes

Defines two public endpoints under `/api/auth`:

- **`POST /api/auth/login`**: Accepts `email` and `password`. Calls `pb.authenticate_user()` which hits PocketBase's `auth-with-password` endpoint. Returns the PocketBase auth response (which includes a `token` and `record`). Returns 401 on invalid credentials.
- **`POST /api/auth/register`**: Accepts `email`, `password`, and optional `name`. Calls `pb.create_user()` which hits PocketBase's user creation endpoint. Returns the new user's `id` and `email`. New users get the default `user` role (no admin access). Returns 400 on validation errors (e.g., duplicate email, weak password).

### `app/routers/chat.py` -- Chat Router

Defines the main chat endpoint:

- **`POST /api/chat`**: Accepts a `ChatRequest` body with `query` (required), `backend` (optional override), `config_id` (optional), and `top_k` (default 5). Requires authentication via `get_current_user`. Calls the `ask()` function from the chat service and appends the user's email to the response. Returns a JSON object with `answer`, `backend`, `config_id`, `sources`, and `user`.

### `app/routers/admin.py` -- Admin Routes

Defines CRUD endpoints for RAG configurations and a stats endpoint, all requiring the `superuser` role:

- **`RAGConfigPayload` model**: A Pydantic model with all 29 configurable fields across all four backends. Used for create and update validation.
- **`GET /api/admin/rag-configs`**: Lists all RAG config records from PocketBase.
- **`GET /api/admin/rag-configs/{config_id}`**: Retrieves a specific config by ID. Returns 404 if not found.
- **`POST /api/admin/rag-configs`**: Creates a new config. The payload is serialized with `exclude_none=True` so that unset optional fields are not sent to PocketBase.
- **`PATCH /api/admin/rag-configs/{config_id}`**: Updates an existing config.
- **`DELETE /api/admin/rag-configs/{config_id}`**: Deletes a config. Returns `{"deleted": true}`.
- **`GET /api/admin/stats`**: Returns usage statistics by calling `get_stats()`.

### `app/services/chat.py` -- Chat Orchestration Service

This is the central orchestration module that ties together configuration, retrieval, and generation:

- **`_ensure_vertexai()`**: Initializes the Vertex AI SDK with the project ID and location from settings. Called once (lazy init) before any GCP API call.
- **`_get_model()`**: Creates a Gemini `GenerativeModel` instance with an optional system instruction. Uses lazy Vertex AI initialization.
- **`get_retriever()`**: Factory function that creates and caches retriever instances. Imports are deferred (inside the function body) so that the Google Cloud SDKs are only loaded when actually needed.
- **`_build_rag_prompt()`**: Constructs the RAG prompt by concatenating the system prompt, a RAG instruction ("Answer using ONLY the context below"), the retrieved chunks (formatted with source and score), and the user's question.
- **`_resolve_config()`**: Fetches a specific PB config by ID, or the active one. Returns `None` if no config exists.
- **`ask()`**: The main entry point. Resolves the config, merges parameters, selects the backend, performs retrieval (if applicable), builds the prompt, calls Gemini, and returns the structured response. The function signature accepts optional overrides for backend, top_k, config_id, model, and temperature.

### `app/services/pocketbase.py` -- PocketBase REST Client

A thin async HTTP client that wraps PocketBase's REST API:

- **`__init__()`**: Stores the base URL from settings and initializes the admin token cache.
- **`_admin_auth()`**: Authenticates as the PocketBase superuser using the email/password from `.env`. Caches the token for subsequent requests. All CRUD operations on `rag_configs` use this admin token because the collection's access rules require the superuser role.
- **`verify_user_token()`**: Validates a user JWT by calling PocketBase's `auth-refresh` endpoint. Returns the user record or `None`.
- **`authenticate_user()`**: Authenticates a user with email/password via `auth-with-password`.
- **`create_user()`**: Creates a new user record with email, password, and name.
- **`get_rag_config()`**: Fetches a single `rag_configs` record by ID.
- **`list_rag_configs()`**: Fetches all `rag_configs` records.
- **`upsert_rag_config()`**: Creates or updates a `rag_configs` record. If `config_id` is provided, it performs a PATCH; otherwise a POST.
- **`delete_rag_config()`**: Deletes a `rag_configs` record by ID.
- **`get_active_rag_config()`**: Returns the first config where `is_active=true`. If none is active, falls back to the most recently created config. Returns `None` if no configs exist.
- **`pb` singleton**: A module-level instance of `PocketBaseClient` imported by other modules.

### `app/services/stats.py` -- Usage Statistics

Provides a `get_stats()` async function that queries PocketBase for usage metrics:

- Total user count, superuser count, and regular user count.
- Total chat history entries.
- Chat count per backend (`none`, `rag_store`, `vertex_search`, `vector_search`).
- The 10 most recent chat entries (ID, created timestamp, backend, and query text).
- Total RAG config count and the currently active config's ID, name, and backend.

All queries use the admin token and PocketBase's REST API with filter and pagination parameters.

### `app/services/notifier.py` -- Error Email Notifications

Provides email notification functionality for unhandled errors:

- **`_get_recipients()`**: Parses the `ERROR_NOTIFY_EMAILS` env var (comma-separated) into a list of email addresses.
- **`send_error_email()`**: Constructs and sends an HTML email containing the error type, message, request context, user email, domain, timestamp, and full Python traceback. Uses SMTP with optional STARTTLS. Returns `True` on success, `False` on failure. If no SMTP host or recipients are configured, the function returns `False` immediately without attempting to send.

The email body is formatted as an HTML table with a dark-themed code block for the traceback, making it readable in email clients.

### `app/retrieval/base.py` -- Retrieval Base Classes

Defines the abstractions used by all retrieval backends:

- **`RetrievedChunk` dataclass**: Represents a single retrieved result with `text`, `score`, `source` (URI or ID), and `metadata` (dict).
- **`RetrievalParams` dataclass**: Contains all backend-specific parameters in a single flat structure. Has 22 fields covering all four backends. Provides two class methods:
  - `from_pb_config(cfg, env_settings)`: Builds params by reading from a PocketBase config dict, falling back to env_settings for empty values.
  - `from_env(env_settings)`: Builds params purely from `.env` defaults.
- **`BaseRetriever` ABC**: Abstract base class with a single `retrieve(query, params)` method that all backend implementations must implement.

### `app/retrieval/rag_store.py` -- RAG Store Retriever

Implements `BaseRetriever` for Vertex AI RAG Store:

- Uses the `vertexai.preview.rag` module (preview API).
- Creates a `RagResource` pointing to the corpus name from params.
- Calls `rag_api.retrieval_query()` with the query text, RAG resources, similarity top-k, and optional vector distance threshold.
- Converts the response contexts into `RetrievedChunk` objects with text, score, source URI, and display name metadata.

### `app/retrieval/vertex_search.py` -- Vertex AI Search Retriever

Implements `BaseRetriever` for Vertex AI Search (Discovery Engine):

- Initializes a `SearchServiceClient` in `__init__()`.
- Builds a `SearchRequest` from params, including optional filter, order_by, boost_spec, query expansion, spell correction, summary spec, and snippet spec.
- Iterates over search results, extracting text from derived_struct_data snippets or falling back to struct_data content.
- Returns `RetrievedChunk` objects with text, relevance score, document name, and structured data metadata.

### `app/retrieval/vector_search.py` -- Vector Search Retriever

Implements `BaseRetriever` for Vertex AI Vector Search (Matching Engine):

- Uses `google.cloud.aiplatform.MatchingEngineIndexEndpoint` for the search endpoint.
- Uses `vertexai.language_models.TextEmbeddingModel` for query embedding.
- Embeds the query text, then calls `find_neighbors()` with the embedding, deployed index ID, number of neighbors, and optional params (approximate neighbor count, fraction leaf nodes, filter restricts).
- Converts filter restricts from JSON dicts to `Namespace` objects.
- Returns `RetrievedChunk` objects with empty text (Vector Search returns IDs only), distance score, match ID as source, and restricts metadata.

### `pb/pb_migrations/1_create_collections.js` -- PocketBase Migration

This JavaScript migration runs automatically when PocketBase starts and creates the database schema:

- **Extends the `users` collection**: Adds a `role` field of type `select` with values `["user", "superuser"]`.
- **Creates `rag_configs` collection**: A base collection with 29 fields covering all four retrieval backends. All CRUD rules require `@request.auth.role = 'superuser'`.
- **Creates `chat_history` collection**: A base collection with fields for user (relation), query, answer, backend, sources (JSON), and config_id. List and view rules restrict records to the owning user. Create rule allows any authenticated user. Update rule is `null` (no updates allowed). Delete rule requires superuser.
- **Rollback (down migration)**: Deletes `chat_history` and `rag_configs` collections.

### `app/static/index.html` -- Admin Chat UI

The admin web interface served at `/admin`. A single-page HTML file with embedded CSS and JavaScript that provides:

- Login/register form.
- Top bar with bot icon, name, backend badge, user email, and sign-out button.
- Settings bar with dropdowns for backend override and config selection.
- Chat message area with user/bot messages, source citations, and typing indicator.
- Input area with auto-growing textarea and send button.

Loads branding from `/api/branding` and configs from `/api/admin/rag-configs` on startup.

### `app/static/user.html` -- User Chat UI

The regular user web interface served at `/`. A single-page HTML file similar to the admin UI but stripped of all admin controls:

- No backend selector dropdown.
- No config selector dropdown.
- No backend badge.
- No source citations in responses.
- Welcome screen with bot icon, welcome title, and subtitle.
- Footer with powered-by text.

Loads branding from `/api/branding` on startup. Sends all chat requests to the active config with no overrides.

### `Dockerfile` -- FastAPI Container Image

A minimal Docker image based on `python:3.12-slim`:

- Sets the working directory to `/app`.
- Copies and installs `requirements.txt` with `--no-cache-dir`.
- Copies the `app/` directory and `.env*` files.
- Runs uvicorn with `--reload` enabled (the reload flag is useful in development when source is mounted via volume, and harmless in production).

### `docker-compose.yml` -- Production Stack

Defines three services:

- **caddy**: Uses `caddy:2-alpine` image. Exposes ports 80 and 443. Mounts the Caddyfile and persistent volumes for certificates and config. Receives the `DOMAIN` env var.
- **fastapi**: Built from the Dockerfile. Loads `.env`. Mounts `./credentials` as read-only at `/app/credentials`. Depends on pocketbase.
- **pocketbase**: Uses `ghcr.io/muchobien/pocketbase:latest`. Exposes port 8090. Mounts a persistent volume for `pb_data` and the migrations directory. Runs with `serve --http=0.0.0.0:8090`.

Three named volumes: `caddy_data`, `caddy_config`, `pb_data`.

### `docker-compose.local.yml` -- Local Development Override

Applied on top of the production compose file for local development:

- **caddy**: Moved to the `production` profile so it does not start locally.
- **fastapi**: Exposes port 8000 directly. Sets `POCKETBASE_URL` explicitly. Mounts `./app` over `/app/app` for live-reloading source changes.
- **pocketbase**: Exposes port 8090 directly.

### `Caddyfile` -- Reverse Proxy Configuration

Defines routing rules for the Caddy reverse proxy:

- `{$DOMAIN:localhost}`: The site address, defaulting to `localhost`. When set to a real domain, Caddy automatically provisions a Let's Encrypt certificate.
- `handle /api/*`: Proxies all API requests to `fastapi:8000`.
- `handle /pb/*`: Strips the `/pb` prefix and proxies to `pocketbase:8090`. This allows accessing PocketBase's admin UI at `/pb/_/`.
- `handle /_/*`: Proxies PocketBase SDK requests directly (for JavaScript SDK clients that expect `/_/` paths).

### `scripts/setup.sh` -- VM Setup Script

A bash script for initial VM provisioning:

1. Copies `.env.example` to `.env` if `.env` does not exist.
2. Creates the `credentials/` directory.
3. Installs Docker via `get.docker.com` if not already installed, and adds the current user to the `docker` group.
4. Starts the full stack with `docker compose up -d --build`.
5. Prints next steps: edit `.env`, create PocketBase admin account, create a RAG config, restart.

### `scripts/run_local.sh` -- Local Development Runner

A bash script that supports two modes:

- **`docker` mode** (default): Checks for `.env` (copies from `.env.local.example` if missing), then runs `docker compose -f docker-compose.yml -f docker-compose.local.yml up --build`. This starts FastAPI and PocketBase without Caddy.
- **`bare` mode**: Checks for `.env`, starts PocketBase binary in the background if not already running (with migrations), then starts FastAPI via uvicorn with `--reload`. Traps EXIT to kill the PocketBase process.

### `scripts/deploy.sh` -- Remote Deployment Script

A bash script for deploying to a GCE VM:

- If no instance name is provided, performs a local deploy: `git pull --ff-only` then `docker compose up -d --build`.
- If an instance name and zone are provided, uses `gcloud compute scp` to sync the repo to the VM (excluding `.env`, `credentials/`, and `pb/pb_data/`), then runs `setup.sh` on the remote VM via `gcloud compute ssh`.

### `tests/conftest.py` -- Test Fixtures

Shared pytest configuration:

- Defines constants for PocketBase URL, API URL, admin credentials, and test user credentials.
- Provides session-scoped fixtures: `event_loop`, `api_url`, `pb_url`, `user_token` (obtained by logging in the test user), and `admin_pb_token` (obtained by authenticating as the PocketBase superuser).
- Provides the `auth_header()` helper function for building Authorization headers.

---

## 5. Retrieval Backends In-Depth

### Backend: None (Direct Gemini)

**How it works**: When the backend is `none`, no retrieval step occurs. The user's query is sent directly to the Gemini LLM. If a system prompt is configured (either in the PocketBase config or as a default), it is set as the model's `system_instruction`, which instructs Gemini to follow those instructions for all responses.

**GCP resources needed**:
- A GCP project with the Vertex AI API enabled.
- A service account with the `Vertex AI User` role.
- No additional data stores or indexes are required.

**Configurable parameters**:
| Parameter | Source | Description |
|---|---|---|
| `llm_model` | PB config or `LLM_MODEL` env | Which Gemini model to use (e.g., `gemini-2.0-flash`, `gemini-2.5-pro`). |
| `temperature` | PB config or `LLM_TEMPERATURE` env | Controls randomness. 0 = deterministic, 2 = maximum randomness. |
| `max_output_tokens` | PB config or `LLM_MAX_OUTPUT_TOKENS` env | Maximum length of the generated response. |
| `top_p` | PB config only | Nucleus sampling. Alternative to temperature for controlling diversity. |
| `system_prompt` | PB config only | Instructions that guide the model's behavior and persona. |

**When to use it**: Use `none` when you want a general-purpose chatbot that does not need to reference specific documents. Good for customer service bots with well-defined personas, creative writing assistants, or any use case where the LLM's built-in knowledge plus a system prompt is sufficient.

### Backend: RAG Store

**How it works**: RAG Store is Google's fully managed RAG service. You create a RAG corpus in Vertex AI, upload documents to it, and Google handles chunking, embedding, storage, and retrieval. When a query comes in, the retriever calls `rag_api.retrieval_query()` with the corpus resource name. The service embeds the query, searches the corpus using approximate nearest neighbor search, and returns the top-k most relevant text chunks with similarity scores and source URIs.

These chunks are then formatted into a RAG prompt (context + question) and sent to Gemini for answer generation.

**GCP resources needed**:
- A GCP project with the Vertex AI API enabled.
- A RAG corpus created via the Vertex AI console or API. The corpus must have documents imported.
- A service account with `Vertex AI User` and `Vertex AI RAG User` roles.
- The full resource name of the corpus: `projects/{project}/locations/{location}/ragCorpora/{id}`.

**Configurable parameters**:
| Parameter | Field | Description |
|---|---|---|
| Corpus name | `rag_corpus_name` | Full resource name of the RAG corpus. Required for this backend. Falls back to `RAG_CORPUS_NAME` env var. |
| Similarity top-k | `rag_similarity_top_k` | Number of chunks to retrieve from the corpus. Overrides the general `top_k`. If not set, uses `top_k`. |
| Distance threshold | `rag_vector_distance_threshold` | Minimum similarity score (0-1). Chunks with scores below this threshold are filtered out. Use this to control quality: higher values return fewer but more relevant results. |

**When to use it**: Use RAG Store when you want the simplest possible RAG setup. You upload documents, Google manages everything else. Best for teams that want managed infrastructure and do not need fine-grained control over embeddings or indexing. Supports PDF, TXT, HTML, and other document formats natively.

### Backend: Vertex AI Search

**How it works**: Vertex AI Search (formerly Discovery Engine) is a managed search service that supports structured data, unstructured documents, and websites. You create a datastore, import data, and the service handles indexing, ranking, and serving. The retriever creates a `SearchRequest` with the serving config and query, plus optional parameters for filtering, boosting, query expansion, and spell correction. The service returns search results with structured data, snippets, and relevance scores.

The retriever extracts text from derived_struct_data snippets (preferred) or falls back to the struct_data content field. These are formatted into a RAG prompt for Gemini.

**GCP resources needed**:
- A GCP project with the Discovery Engine API enabled.
- A Vertex AI Search datastore with data imported.
- A serving config (usually `default_serving_config` within the datastore).
- A service account with `Discovery Engine Viewer` and `Discovery Engine Editor` roles.
- Full resource names for both the serving config and datastore.

**Configurable parameters**:
| Parameter | Field | Description |
|---|---|---|
| Serving config | `vs_serving_config` | Full resource name of the serving config. Required. |
| Datastore | `vs_datastore` | Full resource name of the datastore. Required. |
| Filter | `vs_filter` | Filter expression to narrow results (e.g., `category: ANY("docs")`). |
| Order by | `vs_order_by` | Sort order for results (e.g., `relevance_score desc`). |
| Boost spec | `vs_boost_spec` | JSON boost specification for result ranking. Allows boosting results that match certain conditions. Format: `{"condition_boost_specs": [{"condition": "...", "boost": 0.5}]}`. |
| Query expansion | `vs_query_expansion` | Boolean. When enabled, the service automatically expands the query with related terms to improve recall. |
| Spell correction | `vs_spell_correction` | Boolean. When enabled, the service automatically corrects spelling errors in the query. |
| Summary result count | `vs_summary_result_count` | Number of results to include in the summary (0 = no summary). When set, the service generates a summary across the top results with citations. |
| Snippet result count | `vs_snippet_result_count` | Maximum snippets per result (0 = no snippets). Controls how many text snippets are extracted from each document. |

**When to use it**: Use Vertex AI Search when you need advanced search features like query expansion, spell correction, faceted filtering, boosting, and auto-generated summaries. Best for large document collections, websites, or structured data where search quality and features matter more than raw vector similarity. Supports both structured and unstructured data.

### Backend: Vector Search (Matching Engine)

**How it works**: Vector Search is Google's high-performance approximate nearest neighbor (ANN) search service. Unlike RAG Store and Vertex Search, it works at the embedding level: you pre-compute embeddings for your data, create an index, deploy it to an endpoint, and query it with embedding vectors. The retriever first embeds the user's query using a text embedding model (default: `text-embedding-005`), then calls `find_neighbors()` on the index endpoint to find the most similar vectors.

Vector Search returns match IDs and distances, not text content. The retriever returns `RetrievedChunk` objects with empty text fields. To use this backend for full RAG, you would need to add a text lookup step (e.g., fetching the original document text from a database using the returned IDs).

**GCP resources needed**:
- A GCP project with the Vertex AI API enabled.
- A Vector Search index created and deployed to an index endpoint.
- Pre-computed embeddings for your data, imported into the index.
- A service account with `Vertex AI User` role.
- The full resource name of the index endpoint and the deployed index ID.

**Configurable parameters**:
| Parameter | Field | Description |
|---|---|---|
| Index endpoint | `vec_index_endpoint` | Full resource name of the index endpoint. Required. |
| Deployed index ID | `vec_deployed_index_id` | ID of the deployed index on the endpoint. Required. |
| Embedding model | `vec_embedding_model` | Name of the text embedding model for query embedding. Default: `text-embedding-005`. |
| Approx neighbor count | `vec_approx_neighbor_count` | Number of approximate neighbors to consider (1-1000). Higher values improve accuracy at the cost of latency. |
| Fraction leaf nodes | `vec_fraction_leaf_nodes` | Fraction of leaf nodes to search (0-1). Higher values search more of the index for better recall but slower speed. |
| Filter restricts | `vec_filter_restricts` | JSON array of namespace filters. Each entry has `namespace`, `allow` (list of allowed tokens), and `deny` (list of denied tokens). Used for metadata filtering. |
| Return full datapoint | `vec_return_full_datapoint` | Boolean. When true, returns the full datapoint data with results (not just IDs). |

**When to use it**: Use Vector Search when you need maximum control over the embedding and retrieval process, when you have custom embeddings, when you need sub-millisecond latency at scale, or when you need metadata-based filtering on pre-indexed data. Best for large-scale production systems with millions of embeddings. Requires more setup than RAG Store or Vertex Search since you manage embeddings and indexing yourself.

---

## 6. Database Schema

PocketBase uses SQLite internally. The schema is defined in the migration file `pb/pb_migrations/1_create_collections.js` and consists of three collections.

### Collection: `users` (Extended Built-in)

PocketBase provides a built-in `users` collection with fields for email, password, name, avatar, and standard auth functionality. The migration extends it with one additional field.

| Field | Type | Required | Values | Description |
|---|---|---|---|---|
| `id` | text (auto) | Yes | PocketBase ID | Auto-generated unique identifier. |
| `email` | email | Yes | Valid email | User's email address. Used for login. |
| `password` | password | Yes | Min 8 chars | Hashed password. Managed by PocketBase. |
| `name` | text | No | Any string | Display name. |
| `role` | select | No | `user`, `superuser` | User's role. Defaults to empty (treated as `user`). `superuser` grants access to admin endpoints. |
| `created` | datetime (auto) | Yes | ISO 8601 | Record creation timestamp. |
| `updated` | datetime (auto) | Yes | ISO 8601 | Record last update timestamp. |

**Access rules**: Managed by PocketBase's built-in user collection rules. Users can view and update their own records. Superusers (PocketBase admin) can manage all records.

### Collection: `rag_configs`

Stores retrieval and LLM configuration records. Each record represents a complete configuration set for one backend type.

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | text (auto) | Yes | PocketBase ID | Auto-generated unique identifier. |
| `name` | text | Yes | Non-empty | Display name for the configuration (e.g., "Customer Support Bot"). |
| `description` | text | No | Any | Optional description of what this config is for. |
| `retrieval_backend` | select | Yes | `none`, `rag_store`, `vertex_search`, `vector_search` | Which retrieval backend this config uses. |
| `is_active` | bool | No | true/false | If true, this config is used when no specific config_id is requested. Only one should be active at a time. |
| `llm_model` | text | No | Model name | Gemini model to use (e.g., `gemini-2.0-flash`). |
| `temperature` | number | No | 0-2 | LLM generation temperature. |
| `top_k` | number | No | 1-100 | Number of retrieval results to fetch. |
| `max_output_tokens` | number | No | 1-65536 | Maximum tokens in the LLM response. |
| `system_prompt` | text | No | Any | System instruction for Gemini. Defines the bot's persona and behavior. |
| `top_p` | number | No | 0-1 | Nucleus sampling parameter. |
| `rag_corpus_name` | text | No | Resource name | RAG Store corpus resource name. |
| `rag_similarity_top_k` | number | No | 1-100 | RAG Store similarity search top-k. |
| `rag_vector_distance_threshold` | number | No | 0-1 | RAG Store minimum similarity score. |
| `vs_serving_config` | text | No | Resource name | Vertex Search serving config resource name. |
| `vs_datastore` | text | No | Resource name | Vertex Search datastore resource name. |
| `vs_filter` | text | No | Filter expression | Vertex Search filter string. |
| `vs_order_by` | text | No | Sort expression | Vertex Search result ordering. |
| `vs_boost_spec` | json | No | Object | Vertex Search boost specification. |
| `vs_query_expansion` | bool | No | true/false | Enable Vertex Search query expansion. |
| `vs_spell_correction` | bool | No | true/false | Enable Vertex Search spell correction. |
| `vs_summary_result_count` | number | No | 0-10 | Vertex Search summary result count. |
| `vs_snippet_result_count` | number | No | 0-5 | Vertex Search snippet count per result. |
| `vec_index_endpoint` | text | No | Resource name | Vector Search index endpoint resource name. |
| `vec_deployed_index_id` | text | No | ID string | Vector Search deployed index ID. |
| `vec_embedding_model` | text | No | Model name | Embedding model for Vector Search queries. |
| `vec_approx_neighbor_count` | number | No | 1-1000 | Vector Search approximate neighbor count. |
| `vec_fraction_leaf_nodes` | number | No | 0-1 | Vector Search fraction of leaf nodes to search. |
| `vec_filter_restricts` | json | No | Array of objects | Vector Search namespace filter restricts. |
| `vec_return_full_datapoint` | bool | No | true/false | Return full datapoint data from Vector Search. |
| `created` | datetime (auto) | Yes | ISO 8601 | Record creation timestamp. |
| `updated` | datetime (auto) | Yes | ISO 8601 | Record last update timestamp. |

**Access rules** (all require superuser):
- `listRule`: `@request.auth.role = 'superuser'`
- `viewRule`: `@request.auth.role = 'superuser'`
- `createRule`: `@request.auth.role = 'superuser'`
- `updateRule`: `@request.auth.role = 'superuser'`
- `deleteRule`: `@request.auth.role = 'superuser'`

### Collection: `chat_history`

Stores every chat interaction for analytics and audit purposes.

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | text (auto) | Yes | PocketBase ID | Auto-generated unique identifier. |
| `user` | relation | Yes | -> users, max 1 | Reference to the user who made the query. |
| `query` | text | Yes | Non-empty | The user's question text. |
| `answer` | text | No | Any | The LLM's response text. |
| `backend` | select | No | `none`, `rag_store`, `vertex_search`, `vector_search` | Which retrieval backend was used. |
| `sources` | json | No | Array | JSON array of retrieval source objects (source URI, score, text excerpt). |
| `config_id` | text | No | PB record ID | Which rag_config record was used for this chat. |
| `created` | datetime (auto) | Yes | ISO 8601 | Record creation timestamp. |
| `updated` | datetime (auto) | Yes | ISO 8601 | Record last update timestamp. |

**Access rules**:
- `listRule`: `@request.auth.id = user` -- Users can only list their own chat history.
- `viewRule`: `@request.auth.id = user` -- Users can only view their own records.
- `createRule`: `@request.auth.id != ''` -- Any authenticated user can create records.
- `updateRule`: `null` -- No one can update chat history (immutable).
- `deleteRule`: `@request.auth.role = 'superuser'` -- Only superusers can delete records.

---

## 7. API Reference

### `POST /api/auth/register`

**Description**: Create a new user account.

**Authentication**: None required.

**Request body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "Jane Doe"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string (email) | Yes | Must be a valid email format. Must be unique. |
| `password` | string | Yes | Minimum 8 characters (PocketBase default). |
| `name` | string | No | Display name for the user. |

**Response (200)**:
```json
{
  "id": "abc123xyz",
  "email": "user@example.com"
}
```

**Error responses**:
- `400`: Invalid email, password too short, or email already registered.

---

### `POST /api/auth/login`

**Description**: Authenticate a user and receive a JWT token.

**Authentication**: None required.

**Request body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200)**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "record": {
    "id": "abc123xyz",
    "email": "user@example.com",
    "name": "Jane Doe",
    "role": "user",
    "created": "2025-01-15T10:30:00Z",
    "updated": "2025-01-15T10:30:00Z"
  }
}
```

**Error responses**:
- `401`: Invalid email or password.

---

### `POST /api/chat`

**Description**: Send a message to the chatbot and receive an LLM-generated response, optionally grounded in retrieved context.

**Authentication**: Required. Any authenticated user (user or superuser).

**Request body**:
```json
{
  "query": "What is retrieval-augmented generation?",
  "backend": "rag_store",
  "config_id": "pb_record_id",
  "top_k": 10
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | Yes | -- | The user's question or message. |
| `backend` | string (enum) | No | Use config/env | Override the retrieval backend. Values: `none`, `rag_store`, `vertex_search`, `vector_search`. |
| `config_id` | string | No | Active config | PocketBase record ID of a specific `rag_configs` record to use. |
| `top_k` | integer | No | `5` | Number of retrieval results to fetch (ignored when backend is `none`). |

**Response (200)**:
```json
{
  "answer": "Retrieval-augmented generation (RAG) is a technique that...",
  "backend": "rag_store",
  "config_id": "abc123",
  "sources": [
    {
      "source": "gs://bucket/doc.pdf",
      "score": 0.923,
      "text": "RAG combines retrieval with generation..."
    },
    {
      "source": "gs://bucket/guide.pdf",
      "score": 0.871,
      "text": "The key benefit of RAG is..."
    }
  ],
  "user": "user@example.com"
}
```

| Field | Type | Description |
|---|---|---|
| `answer` | string | The LLM-generated response text. |
| `backend` | string | Which retrieval backend was actually used. |
| `config_id` | string or null | Which PocketBase config was used, or null if none. |
| `sources` | array | Retrieved context chunks. Empty array for `none` backend. Each entry has `source` (URI/ID), `score` (float), and `text` (first 200 chars). |
| `user` | string | Email of the authenticated user. |

**Error responses**:
- `401`: Missing or invalid token.
- `422`: Invalid `backend` value or malformed request body.
- `500`: GCP API error, PocketBase connection error, or other server error.

---

### `GET /api/admin/rag-configs`

**Description**: List all RAG configuration records.

**Authentication**: Required. Superuser only.

**Response (200)**:
```json
[
  {
    "id": "abc123",
    "name": "Default Config",
    "description": "Direct Gemini with custom prompt",
    "retrieval_backend": "none",
    "is_active": true,
    "llm_model": "gemini-2.0-flash",
    "temperature": 0.3,
    "top_k": 5,
    "max_output_tokens": 2048,
    "system_prompt": "You are a helpful assistant.",
    "created": "2025-01-15T10:30:00Z",
    "updated": "2025-01-15T10:30:00Z"
  }
]
```

**Error responses**:
- `401`: Missing or invalid token.
- `403`: User is not a superuser.

---

### `GET /api/admin/rag-configs/{config_id}`

**Description**: Get a specific RAG configuration record by ID.

**Authentication**: Required. Superuser only.

**Path parameters**:
- `config_id` (string): The PocketBase record ID.

**Response (200)**: A single config object (same structure as list items above, with all 29+ fields).

**Error responses**:
- `401`: Missing or invalid token.
- `403`: User is not a superuser.
- `404`: Config not found.

---

### `POST /api/admin/rag-configs`

**Description**: Create a new RAG configuration record.

**Authentication**: Required. Superuser only.

**Request body**: A `RAGConfigPayload` object with up to 29 fields. Only `name` is strictly required. All other fields have defaults.

```json
{
  "name": "My New Config",
  "retrieval_backend": "none",
  "llm_model": "gemini-2.0-flash",
  "temperature": 0.3,
  "system_prompt": "You are a helpful assistant.",
  "is_active": true
}
```

**Response (200)**: The created record with all fields including the generated `id`, `created`, and `updated` timestamps.

**Error responses**:
- `401`: Missing or invalid token.
- `403`: User is not a superuser.
- `422`: Validation error (e.g., missing required `name` field).

---

### `PATCH /api/admin/rag-configs/{config_id}`

**Description**: Update an existing RAG configuration record.

**Authentication**: Required. Superuser only.

**Path parameters**:
- `config_id` (string): The PocketBase record ID.

**Request body**: A `RAGConfigPayload` object. All fields are sent (the full payload model is used), but `exclude_none=True` ensures null optional fields are omitted.

```json
{
  "name": "Updated Config",
  "temperature": 0.7,
  "system_prompt": "New instructions here."
}
```

**Response (200)**: The updated record with all fields.

**Error responses**:
- `401`: Missing or invalid token.
- `403`: User is not a superuser.

---

### `DELETE /api/admin/rag-configs/{config_id}`

**Description**: Delete a RAG configuration record.

**Authentication**: Required. Superuser only.

**Path parameters**:
- `config_id` (string): The PocketBase record ID.

**Response (200)**:
```json
{
  "deleted": true
}
```

**Error responses**:
- `401`: Missing or invalid token.
- `403`: User is not a superuser.

---

### `GET /api/admin/stats`

**Description**: Get usage statistics.

**Authentication**: Required. Superuser only.

**Response (200)**:
```json
{
  "users": {
    "total": 42,
    "superusers": 3,
    "regular": 39
  },
  "chats": {
    "total": 1280,
    "by_backend": {
      "none": 800,
      "rag_store": 300,
      "vertex_search": 150,
      "vector_search": 30
    }
  },
  "recent_chats": [
    {
      "id": "rec123",
      "created": "2025-01-15T14:30:00Z",
      "backend": "none",
      "query": "What is RAG?"
    }
  ],
  "configs": {
    "total": 4,
    "active": {
      "id": "cfg456",
      "name": "Default",
      "retrieval_backend": "none"
    }
  }
}
```

**Error responses**:
- `401`: Missing or invalid token.
- `403`: User is not a superuser.

---

### `GET /api/health`

**Description**: Health check endpoint.

**Authentication**: None required.

**Response (200)**:
```json
{
  "status": "ok"
}
```

---

### `GET /api/branding`

**Description**: Get branding information for the UIs.

**Authentication**: None required.

**Response (200)**:
```json
{
  "bot_name": "Chat Assistant",
  "bot_icon_url": "https://example.com/logo.png",
  "welcome_title": "How can I help you?",
  "welcome_subtitle": "Ask me anything.",
  "powered_by_text": "Powered by AI"
}
```

---

### `GET /api/docs`

**Description**: Swagger UI for interactive API documentation.

**Authentication**: None required.

---

### `GET /`

**Description**: Serves the regular user chat UI (`user.html`).

**Authentication**: None required (the page itself loads; the chat API requires auth).

---

### `GET /admin`

**Description**: Serves the admin chat UI (`index.html`).

**Authentication**: None required (the page itself loads; admin API endpoints require superuser auth).

---

## 8. Authentication & Authorization

### How PocketBase JWT Auth Works

The project uses PocketBase as the identity provider. PocketBase implements JWT-based authentication:

1. **Registration**: When a user registers via `POST /api/auth/register`, the FastAPI backend calls PocketBase's user creation endpoint. PocketBase hashes the password, stores the record in SQLite, and returns the user data.

2. **Login**: When a user logs in via `POST /api/auth/login`, the FastAPI backend calls PocketBase's `auth-with-password` endpoint. PocketBase validates the credentials and returns a JWT token along with the user record. The token is a standard JWT signed with PocketBase's secret key.

3. **Token validation**: For every authenticated request to FastAPI, the `get_current_user` dependency extracts the Bearer token from the `Authorization` header and calls PocketBase's `auth-refresh` endpoint. This endpoint validates the token's signature and expiration, and returns the current user record if valid. This approach ensures that FastAPI does not need to know PocketBase's signing secret -- it delegates validation entirely to PocketBase.

4. **Token lifetime**: PocketBase JWTs have a configurable expiration (default is typically 14 days for user tokens). The `auth-refresh` call also refreshes the token, extending the session.

### User Roles

The system has two roles, stored in the `role` field of the `users` collection:

**`user` (default)**:
- Can register and log in.
- Can use the chat endpoint (`POST /api/chat`).
- Can view and list their own chat history (via PocketBase access rules).
- Can access the user UI at `/`.
- Cannot access admin endpoints.
- Cannot view or manage RAG configurations.
- Cannot view statistics.
- Cannot delete chat history.

**`superuser`**:
- All permissions of `user`, plus:
- Can access all admin endpoints (`/api/admin/*`).
- Can create, read, update, and delete RAG configurations.
- Can view usage statistics.
- Can delete any chat history record (via PocketBase access rules).
- Can use the admin UI at `/admin` with backend/config selectors and source citations.
- Receives error notification emails (if configured in `ERROR_NOTIFY_EMAILS`).

### How to Promote a User to Superuser

New users are created with no role (treated as `user`). To promote a user to superuser:

1. Open the PocketBase admin UI at `http://localhost:8090/_/` (local) or `https://your-domain.com/pb/_/` (production).
2. Log in with the PocketBase admin credentials (set in `.env` as `POCKETBASE_ADMIN_EMAIL` and `POCKETBASE_ADMIN_PASSWORD`).
3. Navigate to the `users` collection.
4. Find the user record.
5. Set the `role` field to `superuser`.
6. Save the record.

The change takes effect on the user's next API request (the token validation returns the updated record).

### What Each Role Can Access

| Endpoint | User | Superuser |
|---|---|---|
| `POST /api/auth/register` | Yes (public) | Yes (public) |
| `POST /api/auth/login` | Yes (public) | Yes (public) |
| `GET /api/health` | Yes (public) | Yes (public) |
| `GET /api/branding` | Yes (public) | Yes (public) |
| `POST /api/chat` | Yes | Yes |
| `GET /api/admin/rag-configs` | No (403) | Yes |
| `GET /api/admin/rag-configs/{id}` | No (403) | Yes |
| `POST /api/admin/rag-configs` | No (403) | Yes |
| `PATCH /api/admin/rag-configs/{id}` | No (403) | Yes |
| `DELETE /api/admin/rag-configs/{id}` | No (403) | Yes |
| `GET /api/admin/stats` | No (403) | Yes |

---

## 9. Branding & Customization

### Branding Variables

Each deployment of the chatbot can have its own visual identity, controlled entirely through environment variables in `.env`:

| Variable | Default | Where It Appears |
|---|---|---|
| `BOT_NAME` | `Chat Assistant` | Page title (browser tab), login screen heading, top bar title in both UIs. |
| `BOT_ICON_URL` | (empty) | Login screen icon, welcome area icon, top bar icon, browser favicon. Must be a URL to a PNG, SVG, or other web-compatible image. When empty, no icon is displayed. |
| `WELCOME_TITLE` | `How can I help you?` | Large heading on the welcome screen that appears before the first message in the user UI. |
| `WELCOME_SUBTITLE` | `Ask me anything.` | Smaller descriptive text below the welcome title. |
| `POWERED_BY_TEXT` | (empty) | Footer text at the bottom of the user chat UI. When empty, no footer is shown. |

### How to Customize Per Clone

1. Edit the `.env` file on each deployment:
   ```env
   BOT_NAME=Acme Support
   BOT_ICON_URL=https://cdn.example.com/acme-logo.png
   WELCOME_TITLE=Welcome to Acme Support
   WELCOME_SUBTITLE=Ask about our products, billing, or anything else.
   POWERED_BY_TEXT=Powered by Acme AI
   ```

2. Restart the FastAPI service:
   ```bash
   docker compose restart fastapi
   ```

3. Reload the browser. The UIs fetch branding from `/api/branding` on every page load, so the changes appear immediately.

### Where Branding Appears in the UIs

**User UI (`/`)**:
- **Login screen**: The bot icon (if set) appears above the login form. The bot name appears as the heading.
- **Welcome screen**: Before the first message, a large centered area shows the bot icon, welcome title, and welcome subtitle. This area disappears once the user sends their first message.
- **Top bar**: Shows the bot icon and bot name on the left side.
- **Footer**: Shows the powered-by text at the bottom of the chat area.
- **Browser tab**: The page title is set to the bot name.

**Admin UI (`/admin`)**:
- **Login screen**: Same as user UI.
- **Top bar**: Shows the bot icon and bot name.
- **Browser tab**: The page title is set to the bot name.
- The admin UI does not show the welcome screen or powered-by footer.

### How Branding is Served

The branding values are served via a public endpoint:

```
GET /api/branding
```

This endpoint requires no authentication, so the UIs can fetch branding before the user logs in (for the login screen). The endpoint reads directly from the `settings` singleton, which loads values from `.env` at startup.

---

## 10. Error Handling & Notifications

### Error Middleware

The FastAPI application includes a global error-handling middleware defined in `app/main.py`. This middleware wraps every incoming HTTP request:

```
Request -> error_notify_middleware -> route handler -> Response
                                      |
                                      v (if exception)
                              Log error + Send email + Return 500 JSON
```

When an unhandled exception occurs in any route handler:

1. The exception is logged using Python's standard logging with `logger.exception()`, which captures the full traceback.
2. The middleware attempts to extract the user's email from `request.state.user` (if the auth middleware has already set it).
3. The `send_error_email()` function is called with the exception, the request context (method and path), and the user email.
4. A generic `{"detail": "Internal server error"}` JSON response with status code 500 is returned to the client.
5. If the email sending itself fails, the failure is silently caught (so the error middleware never crashes).

### SMTP Email Notification System

The notification system is implemented in `app/services/notifier.py` and uses Python's built-in `smtplib` and `email` modules.

**Configuration** (in `.env`):
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=alerts@example.com
SMTP_TLS=true
ERROR_NOTIFY_EMAILS=admin1@example.com,admin2@example.com
```

**When notifications are sent**: Only when an unhandled exception occurs in any API endpoint. Handled errors (e.g., 401, 403, 404 returned by route handlers) do not trigger notifications.

**When notifications are skipped**:
- If `SMTP_HOST` is empty (email is disabled).
- If `ERROR_NOTIFY_EMAILS` is empty (no recipients configured).
- If the email sending fails (logged but not re-raised).

### Email Format and Content

The error notification email is sent as HTML and contains the following:

**Subject line**: `[{BOT_NAME}] Error: {ExceptionType}`

**Body** (HTML formatted):
| Field | Content |
|---|---|
| Time | UTC timestamp in ISO 8601 format |
| Error | Exception class name and message (e.g., `ValueError: Invalid config`) |
| Context | HTTP method and path (e.g., `POST /api/chat`) |
| User | Email of the user who triggered the error, or "N/A" |
| Domain | The configured domain name |
| Traceback | Full Python traceback in a dark-themed code block |

The email is constructed as a MIME multipart message with HTML content type, sent via SMTP with optional STARTTLS encryption.

---

## 11. Statistics & Monitoring

### Stats Endpoint

The `GET /api/admin/stats` endpoint provides a snapshot of the system's usage. It is accessible only to superusers.

### Available Metrics

**User statistics**:
- `users.total`: Total number of registered users.
- `users.superusers`: Number of users with the `superuser` role.
- `users.regular`: Number of non-superuser users (calculated as `total - superusers`).

**Chat statistics**:
- `chats.total`: Total number of chat history records.
- `chats.by_backend.none`: Number of chats using direct Gemini (no retrieval).
- `chats.by_backend.rag_store`: Number of chats using RAG Store.
- `chats.by_backend.vertex_search`: Number of chats using Vertex AI Search.
- `chats.by_backend.vector_search`: Number of chats using Vector Search.

**Recent activity**:
- `recent_chats`: Array of the 10 most recent chat records, each containing `id`, `created` timestamp, `backend`, and `query` text. Ordered by creation date descending.

**Configuration statistics**:
- `configs.total`: Total number of RAG config records.
- `configs.active`: Object with `id`, `name`, and `retrieval_backend` of the currently active config, or `null` if no config is active.

### How Stats Are Gathered

All statistics are fetched from PocketBase via REST API calls using the admin token. The stats service (`app/services/stats.py`) makes multiple API calls to PocketBase:

1. Total users: `GET /api/collections/users/records?perPage=1` (reads `totalItems`).
2. Superusers: Same endpoint with `filter=role='superuser'`.
3. Total chats: `GET /api/collections/chat_history/records?perPage=1`.
4. Chats per backend: Four separate calls with `filter=backend='{backend}'`.
5. Recent chats: `GET /api/collections/chat_history/records?sort=-created&perPage=10&fields=id,created,backend,query`.
6. Config count: `GET /api/collections/rag_configs/records?perPage=1`.
7. Active config: `GET /api/collections/rag_configs/records?filter=is_active=true&perPage=1&fields=id,name,retrieval_backend`.

All calls use `perPage=1` where only the count is needed, reading `totalItems` from the response metadata rather than fetching all records.

---

## 12. Prerequisites

### For Local Development

**Docker mode (recommended)**:
- Docker Engine 20.10 or later.
- Docker Compose V2 (included with Docker Desktop, or install the `docker-compose-plugin` package).
- A text editor for editing `.env`.
- 2 GB of free RAM minimum (PocketBase is lightweight, but the Python dependencies and Docker overhead add up).

**Bare-metal mode**:
- Python 3.10 or later (3.12 recommended, matching the Dockerfile).
- pip for installing Python dependencies.
- The PocketBase binary (download from https://pocketbase.io/docs/). Place it in your PATH or in the `./pb/` directory.
- A text editor for editing `.env`.

**For both modes**:
- A Google Cloud project with the Vertex AI API enabled (required even for `none` backend, since the Gemini LLM call goes through Vertex AI).
- A GCP service account key JSON file with at minimum the `Vertex AI User` role.
- `GOOGLE_APPLICATION_CREDENTIALS` set to the path of this key file.

### For VM Deployment (Production)

- A Google Compute Engine (GCE) VM or any Linux server with:
  - Ubuntu 20.04+ or Debian 11+ (the setup script uses `get.docker.com` which supports these).
  - At least 2 vCPUs and 4 GB RAM (e2-medium or larger).
  - At least 20 GB of disk space.
  - A public IP address.
  - Ports 80 and 443 open in the firewall.
- A domain name pointed to the VM's public IP (for Caddy's automatic HTTPS via Let's Encrypt).
- SSH access to the VM.
- Git installed on the VM (for cloning the repo).

### GCP Requirements

**APIs to enable** (in the Google Cloud Console under APIs & Services):
- Vertex AI API (`aiplatform.googleapis.com`) -- Required for all backends.
- Discovery Engine API (`discoveryengine.googleapis.com`) -- Required only for `vertex_search` backend.

**Service account permissions**:
| Role | When Needed |
|---|---|
| `Vertex AI User` | Always (for Gemini LLM calls and RAG Store) |
| `Discovery Engine Viewer` | For `vertex_search` backend |
| `Discovery Engine Editor` | For `vertex_search` backend (if creating datastores via API) |

**Backend-specific resources**:

For `rag_store`:
- A RAG corpus created in Vertex AI with documents imported.

For `vertex_search`:
- A Vertex AI Search datastore with data imported.
- A serving config (automatically created with the datastore).

For `vector_search`:
- A Vector Search index with embeddings imported.
- The index deployed to an index endpoint.

---

## 13. Installation & Setup

### Local Development

#### Option A: Docker (Recommended)

**Step 1: Clone the repository**
```bash
git clone <repo-url> && cd chatbot
```

**Step 2: Create the `.env` file**
```bash
cp .env.local.example .env
```

**Step 3: Edit `.env`**

Open `.env` in a text editor and set at minimum:
```env
GCP_PROJECT_ID=your-gcp-project-id
POCKETBASE_ADMIN_EMAIL=admin@example.com
POCKETBASE_ADMIN_PASSWORD=a-secure-password
```

If you have a GCP service account key:
```env
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
```
And place the key file:
```bash
mkdir -p credentials
cp /path/to/your/service-account.json credentials/service-account.json
```

**Step 4: Start the services**
```bash
bash scripts/run_local.sh docker
```

This runs `docker compose -f docker-compose.yml -f docker-compose.local.yml up --build`, which starts FastAPI on port 8000 and PocketBase on port 8090 (Caddy is disabled).

**Step 5: Create the PocketBase admin account**

Open http://localhost:8090/_/ in your browser. PocketBase will prompt you to create the first admin account. Use the same email and password you set in `.env` for `POCKETBASE_ADMIN_EMAIL` and `POCKETBASE_ADMIN_PASSWORD`.

**Step 6: Create a test user**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "testpassword", "name": "Test User"}'
```

**Step 7: Promote the user to superuser (optional)**

In the PocketBase admin UI (http://localhost:8090/_/), navigate to the `users` collection, find your user, and set the `role` field to `superuser`.

**Step 8: Create a RAG configuration**

Log in to get a token:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "testpassword"}'
```

Create a config using the token:
```bash
curl -X POST http://localhost:8000/api/admin/rag-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Default",
    "retrieval_backend": "none",
    "system_prompt": "You are a helpful assistant.",
    "is_active": true
  }'
```

**Step 9: Verify everything works**

- Open http://localhost:8000 -- you should see the user chat UI with the login screen.
- Open http://localhost:8000/admin -- you should see the admin chat UI.
- Open http://localhost:8000/api/docs -- you should see the Swagger documentation.
- Open http://localhost:8090/_/ -- you should see the PocketBase admin dashboard.
- Test the health endpoint: `curl http://localhost:8000/api/health` should return `{"status": "ok"}`.
- Test the branding endpoint: `curl http://localhost:8000/api/branding` should return the branding settings.

#### Option B: Bare-metal (No Docker)

**Step 1: Clone the repository**
```bash
git clone <repo-url> && cd chatbot
```

**Step 2: Install Python dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Install PocketBase**

Download the PocketBase binary for your OS from https://pocketbase.io/docs/. Place it in your system PATH or in the `./pb/` directory.

**Step 4: Create the `.env` file**
```bash
cp .env.local.example .env
```

Edit `.env` and set `POCKETBASE_URL=http://localhost:8090` (this is the default in the local template).

**Step 5: Start the services**
```bash
bash scripts/run_local.sh bare
```

This script:
1. Checks if PocketBase is already running on port 8090.
2. If not, starts PocketBase in the background with the migrations directory pointed to `./pb/pb_migrations`.
3. Starts FastAPI via uvicorn with `--reload` on port 8000.

**Step 6: Follow steps 5-9 from Option A** to set up the PocketBase admin, create users, and verify.

### VM Deployment (Google Compute Engine)

#### Step 1: Create a VM

In the Google Cloud Console or via `gcloud`:

```bash
gcloud compute instances create chatbot-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server
```

Ensure firewall rules allow ports 80 and 443:
```bash
gcloud compute firewall-rules create allow-http --allow=tcp:80 --target-tags=http-server
gcloud compute firewall-rules create allow-https --allow=tcp:443 --target-tags=https-server
```

#### Step 2: SSH into the VM

```bash
gcloud compute ssh chatbot-vm --zone=us-central1-a
```

#### Step 3: Clone the repository

```bash
git clone <repo-url> && cd chatbot
```

#### Step 4: Run the setup script

```bash
bash scripts/setup.sh
```

This script will:
1. Copy `.env.example` to `.env` if it does not exist.
2. Create the `credentials/` directory.
3. Install Docker if not already installed.
4. Start the full stack (Caddy + FastAPI + PocketBase) with `docker compose up -d --build`.

#### Step 5: Configure `.env`

```bash
nano .env
```

Set these required values:
```env
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
POCKETBASE_ADMIN_EMAIL=admin@yourdomain.com
POCKETBASE_ADMIN_PASSWORD=a-very-secure-password
DOMAIN=chat.yourdomain.com
```

Set any additional values for retrieval backends, LLM settings, branding, and SMTP.

#### Step 6: Set up GCP credentials

Copy your service account key to the VM:
```bash
mkdir -p credentials
# From your local machine:
gcloud compute scp /path/to/service-account.json chatbot-vm:~/chatbot/credentials/service-account.json --zone=us-central1-a
```

Or create the file directly on the VM:
```bash
nano credentials/service-account.json
# Paste the JSON content
```

#### Step 7: Set up a domain with Caddy HTTPS

1. Point your domain's DNS A record to the VM's external IP address.
2. Set `DOMAIN=chat.yourdomain.com` in `.env`.
3. Restart the stack:
   ```bash
   docker compose up -d --build
   ```
4. Caddy will automatically obtain a Let's Encrypt certificate for your domain. This may take a few seconds on first request.
5. Verify by opening `https://chat.yourdomain.com` in your browser.

If DNS is not yet propagated or you do not have a domain, you can use `DOMAIN=localhost` and access the VM via its IP address on port 80 (HTTP only).

#### Step 8: Create the first admin account

**Option A: Via the PocketBase admin UI**

Open `https://chat.yourdomain.com/pb/_/` in your browser. PocketBase will prompt you to create the first admin account.

**Option B: Via command line**
```bash
docker compose exec pocketbase ./pocketbase superuser upsert admin@example.com your-password
```

#### Step 9: Create a user, promote to superuser, and create a RAG config

Follow the same steps as in the local development section (Steps 6-8), using your domain instead of `localhost:8000`.

---

## 14. Cloning for Multiple Deployments

The project is designed to be cloned and customized for different teams, projects, or customers. Each clone runs as an independent instance with its own PocketBase database, users, configurations, and branding.

### How to Clone and Customize

1. **Clone the repo on each VM**:
   ```bash
   git clone <repo-url> chatbot-team-alpha
   cd chatbot-team-alpha
   ```

2. **Run the setup script**:
   ```bash
   bash scripts/setup.sh
   ```

3. **Edit `.env` with clone-specific values**:
   ```bash
   nano .env
   ```

### What to Change Per Clone

**Required per-clone changes in `.env`**:

| Variable | Why It Must Change |
|---|---|
| `DOMAIN` | Each clone needs its own domain (e.g., `alpha.example.com`, `beta.example.com`) for Caddy to issue the correct TLS certificate. |
| `POCKETBASE_ADMIN_EMAIL` | Each PocketBase instance should have its own admin credentials. |
| `POCKETBASE_ADMIN_PASSWORD` | Same as above. |

**Optional per-clone customizations in `.env`**:

| Variable | What to Customize |
|---|---|
| `BOT_NAME` | Different name per team (e.g., "Alpha Support", "Beta Docs Bot"). |
| `BOT_ICON_URL` | Different logo per team. |
| `WELCOME_TITLE` | Different welcome message. |
| `WELCOME_SUBTITLE` | Different subtitle. |
| `POWERED_BY_TEXT` | Different footer. |
| `DEFAULT_RETRIEVAL_BACKEND` | Each clone can use a different default backend. |
| `RAG_CORPUS_NAME` | Each clone can point to a different RAG corpus. |
| `VERTEX_SEARCH_DATASTORE` | Each clone can query a different datastore. |
| `VERTEX_SEARCH_SERVING_CONFIG` | Each clone can use a different serving config. |
| `VECTOR_SEARCH_INDEX_ENDPOINT` | Each clone can use a different vector index. |
| `VECTOR_SEARCH_DEPLOYED_INDEX_ID` | Each clone can use a different deployed index. |
| `LLM_MODEL` | Each clone can use a different Gemini model. |
| `SMTP_HOST` / `SMTP_*` | Each clone can have its own error notification setup. |
| `ERROR_NOTIFY_EMAILS` | Different admins per clone. |

**Shared across clones** (typically the same):

| Variable | Why It Is Shared |
|---|---|
| `GCP_PROJECT_ID` | All clones can share the same GCP project (or use different ones). |
| `GCP_LOCATION` | Usually the same region for all clones. |
| `GOOGLE_APPLICATION_CREDENTIALS` | All clones can share the same service account (with appropriate permissions). |

### Shared vs. Independent PocketBase Instances

Each clone has its own PocketBase instance with its own SQLite database. This means:

- **Users are independent**: Each clone has its own user accounts. A user registered on Clone A does not exist on Clone B.
- **Configurations are independent**: Each clone has its own `rag_configs` records. Changing a config on Clone A does not affect Clone B.
- **Chat history is independent**: Each clone stores its own chat history.
- **Roles are independent**: A superuser on Clone A is not a superuser on Clone B.

If you need shared user accounts across clones, you would need to either:
- Point multiple FastAPI instances at the same PocketBase instance (by setting `POCKETBASE_URL` to a shared PocketBase host).
- Use an external identity provider and modify the auth layer.

For most use cases, independent PocketBase instances per clone are the correct choice.

### Remote Deploy to Multiple VMs

Use the deploy script to push code to a specific VM:

```bash
# Deploy to VM "alpha" in us-central1-a
bash scripts/deploy.sh alpha-vm us-central1-a

# Deploy to VM "beta" in europe-west1-b
bash scripts/deploy.sh beta-vm europe-west1-b
```

The deploy script syncs code but excludes `.env`, `credentials/`, and `pb/pb_data/`. This means each VM's configuration, secrets, and database are preserved across deployments.

---

## 15. Testing

### Test Suite Overview

The project includes a comprehensive test suite in the `tests/` directory. Tests are written using `pytest` and `httpx`, and run against a live FastAPI server and PocketBase instance (not mocked).

### Test Files

| File | What It Tests | Number of Tests |
|---|---|---|
| `tests/conftest.py` | Shared fixtures and configuration. Not a test file. | -- |
| `tests/test_health.py` | Service availability: FastAPI health endpoint, PocketBase health endpoint, user UI serving, admin UI serving, branding endpoint. | 5 |
| `tests/test_auth.py` | Authentication flow: successful login, wrong password rejection, register-and-login flow, chat requires auth, chat rejects bad token. | 5 |
| `tests/test_rag_configs.py` | Full CRUD for all four backend types (none, rag_store, vertex_search, vector_search). Create and read back all fields, update and verify, list, delete and verify, 404 for nonexistent IDs. Also tests that regular users are blocked from admin endpoints. | 14 (4 parameterized x 2, plus list, delete, 404, and non-superuser tests) |
| `tests/test_retrieval_params.py` | Unit tests for `RetrievalParams` construction. Tests `from_env()` defaults, `from_pb_config()` with overrides, fallback to env when PB fields are empty, backend-specific params (rag_store, vertex_search, vector_search), edge cases (zero threshold, empty lists, null values). | 12 |
| `tests/test_chat_integration.py` | Chat endpoint integration: round-trip storage and retrieval for all four backend configs, active config selection, input validation (invalid backend returns 422, empty query handling, nonexistent config_id handling). | 7 |

### How to Run Tests

**Prerequisites**: Both PocketBase and FastAPI must be running locally.

1. Start the services:
   ```bash
   bash scripts/run_local.sh docker
   # or
   bash scripts/run_local.sh bare
   ```

2. Ensure a test user exists. The tests expect:
   - A user with email `test@test.com` and password `testtest123`.
   - This user should have the `superuser` role (for admin endpoint tests).
   - A PocketBase admin with email `admin@admin.com` and password `adminadmin123`.

3. Install test dependencies:
   ```bash
   pip install pytest httpx
   ```

4. Run all tests:
   ```bash
   python -m pytest tests/ -v
   ```

5. Run a specific test file:
   ```bash
   python -m pytest tests/test_health.py -v
   python -m pytest tests/test_rag_configs.py -v
   ```

6. Run a specific test class or method:
   ```bash
   python -m pytest tests/test_rag_configs.py::TestRAGConfigCRUD::test_create_and_read -v
   python -m pytest tests/test_retrieval_params.py::TestRetrievalParamsFromPBConfig -v
   ```

### What Each Test File Covers

**`test_health.py`**: Verifies that the infrastructure is running. Tests that `GET /api/health` returns 200 with `{"status": "ok"}`, that PocketBase's health endpoint responds, that `GET /` serves the user UI HTML (checks for `chat-screen` in the response), that `GET /admin` serves the admin UI HTML (checks for `RAG Chatbot`), and that `GET /api/branding` returns the expected fields.

**`test_auth.py`**: Tests the authentication lifecycle. Verifies successful login returns a token and user record, wrong password returns 401, the full register-then-login flow works (using a random email), requests to `/api/chat` without a token are rejected (401/403), and requests with an invalid token are rejected (401).

**`test_rag_configs.py`**: Tests the admin CRUD API for RAG configurations. For each of the four backend types, it creates a config with all backend-specific parameters, reads it back and asserts every field matches, updates it and verifies the changes, and deletes it. Also tests listing multiple configs, deleting and confirming 404 on re-fetch, 404 for nonexistent IDs, and that regular (non-superuser) users get 403 from admin endpoints.

**`test_retrieval_params.py`**: Pure unit tests (no live services needed beyond importing the module). Tests that `from_env()` correctly reads defaults from the settings object, that `from_pb_config()` overrides env values when PB config has values, that empty PB fields fall back to env, that each backend's specific parameters are correctly populated, and edge cases like zero thresholds, empty filter lists, and null boost specs.

**`test_chat_integration.py`**: Integration tests that create configs via the admin API, read them back to verify storage, test active config selection, and validate the chat endpoint's input handling (invalid backend returns 422, empty query does not crash, nonexistent config_id does not cause a validation error).

### How to Add New Tests

1. Create a new file in `tests/` following the naming convention `test_<feature>.py`.
2. Import fixtures from `conftest.py`:
   ```python
   from tests.conftest import auth_header
   ```
3. Use the session-scoped fixtures (`api_url`, `pb_url`, `user_token`, `admin_pb_token`) provided by conftest.
4. For tests that need a superuser token, either use the `admin_pb_token` fixture or create a module-scoped fixture that logs in as the test user.
5. Clean up any created resources (configs, users) in the test or via a fixture teardown.
6. Run your new tests: `python -m pytest tests/test_your_feature.py -v`.

---

## 16. Environment Variables Reference

The complete list of all environment variables, their types, default values, and descriptions.

### Google Cloud

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `GCP_PROJECT_ID` | string | (empty) | Yes | Your Google Cloud project ID. Required for all Vertex AI API calls. |
| `GCP_LOCATION` | string | `us-central1` | No | GCP region for Vertex AI resources. Must match the region of your data stores and indexes. |
| `GOOGLE_APPLICATION_CREDENTIALS` | string | (empty) | Yes | Path to the GCP service account JSON key file. Inside the Docker container, this should be `/app/credentials/service-account.json`. |

### Retrieval Backend

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `DEFAULT_RETRIEVAL_BACKEND` | enum | `none` | No | Default retrieval backend when no PocketBase config or per-request override specifies one. Values: `none`, `rag_store`, `vertex_search`, `vector_search`. |

### Vertex RAG Store

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `RAG_CORPUS_NAME` | string | (empty) | If using `rag_store` | Full resource name of the RAG corpus. Format: `projects/{project}/locations/{location}/ragCorpora/{corpus_id}`. Can be overridden per-config in PocketBase. |

### Vertex AI Search

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `VERTEX_SEARCH_DATASTORE` | string | (empty) | If using `vertex_search` | Full resource name of the Vertex Search datastore. Can be overridden per-config in PocketBase. |
| `VERTEX_SEARCH_SERVING_CONFIG` | string | (empty) | If using `vertex_search` | Full resource name of the serving config. Can be overridden per-config in PocketBase. |

### Vector Search

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `VECTOR_SEARCH_INDEX_ENDPOINT` | string | (empty) | If using `vector_search` | Full resource name of the Vector Search index endpoint. Can be overridden per-config in PocketBase. |
| `VECTOR_SEARCH_DEPLOYED_INDEX_ID` | string | (empty) | If using `vector_search` | ID of the deployed index on the endpoint. Can be overridden per-config in PocketBase. |
| `EMBEDDING_MODEL` | string | `text-embedding-005` | No | Name of the text embedding model used for Vector Search query embedding. Can be overridden per-config in PocketBase. |

### Vertex AI LLM

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `LLM_MODEL` | string | `gemini-2.0-flash` | No | Gemini model name. Can be overridden per-config in PocketBase. |
| `LLM_TEMPERATURE` | float | `0.3` | No | Generation temperature (0-2). Lower values produce more deterministic outputs. Can be overridden per-config. |
| `LLM_MAX_OUTPUT_TOKENS` | integer | `2048` | No | Maximum tokens in the LLM response (1-65536). Can be overridden per-config. |

### PocketBase

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `POCKETBASE_URL` | string | `http://pocketbase:8090` | Yes | PocketBase server URL. Use `http://pocketbase:8090` for Docker and `http://localhost:8090` for bare-metal local dev. |
| `POCKETBASE_ADMIN_EMAIL` | string | (empty) | Yes | PocketBase superuser email. Used by the FastAPI backend to authenticate with PocketBase for admin operations (reading configs, etc.). |
| `POCKETBASE_ADMIN_PASSWORD` | string | (empty) | Yes | PocketBase superuser password. |

### FastAPI

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `API_HOST` | string | `0.0.0.0` | No | Host address for uvicorn to bind to. `0.0.0.0` listens on all interfaces. |
| `API_PORT` | integer | `8000` | No | Port for uvicorn to bind to. |
| `API_WORKERS` | integer | `2` | No | Number of uvicorn worker processes. Increase for higher throughput on multi-core VMs. |
| `LOG_LEVEL` | string | `info` | No | Python logging level. Values: `debug`, `info`, `warning`, `error`, `critical`. |

### Caddy

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `DOMAIN` | string | `localhost` | Yes (production) | Domain name for Caddy's HTTPS certificate. Set to `localhost` for local development (Caddy serves HTTP). Set to your real domain (e.g., `chat.example.com`) for production (Caddy auto-provisions Let's Encrypt certificates). |

### Branding

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `BOT_NAME` | string | `Chat Assistant` | No | Bot display name. Appears in page titles, headings, and top bars. |
| `BOT_ICON_URL` | string | (empty) | No | URL to the bot icon image (PNG, SVG, etc.). Used on login screen, welcome area, top bar, and as favicon. Leave empty for no icon. |
| `WELCOME_TITLE` | string | `How can I help you?` | No | Large heading text on the user UI welcome screen. |
| `WELCOME_SUBTITLE` | string | `Ask me anything.` | No | Smaller text below the welcome title. |
| `POWERED_BY_TEXT` | string | (empty) | No | Footer text in the user UI. Leave empty for no footer. |

### Error Email Notifications

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `SMTP_HOST` | string | (empty) | No | SMTP server hostname. Leave empty to disable email notifications entirely. |
| `SMTP_PORT` | integer | `587` | No | SMTP server port. 587 is the standard STARTTLS port. Use 465 for implicit TLS (and set `SMTP_TLS=false` since implicit TLS does not use STARTTLS). |
| `SMTP_USER` | string | (empty) | No | SMTP login username. Typically your email address. |
| `SMTP_PASSWORD` | string | (empty) | No | SMTP login password. For Gmail, use an App Password. |
| `SMTP_FROM` | string | (empty) | No | Sender email address for notifications. Falls back to `SMTP_USER` if not set. |
| `SMTP_TLS` | boolean | `true` | No | Whether to use STARTTLS encryption. Set to `true` for port 587, `false` for unencrypted or if using implicit TLS on port 465 with a different mechanism. |
| `ERROR_NOTIFY_EMAILS` | string | (empty) | No | Comma-separated list of email addresses to receive error notifications. Typically superuser email addresses. |

---

## 17. Troubleshooting

### Common Issues and Solutions

**Issue: `docker compose up` fails with "port already in use"**

Cause: Another service is using port 80, 443, 8000, or 8090.

Solution:
```bash
# Check what is using the port
lsof -i :8000
# Or on Linux:
ss -tlnp | grep 8000

# Stop the conflicting service, or change the port in docker-compose.local.yml
```

**Issue: FastAPI cannot connect to PocketBase**

Cause: The `POCKETBASE_URL` does not match the actual PocketBase address.

Solution:
- In Docker: Use `http://pocketbase:8090` (the Docker service name).
- In bare-metal: Use `http://localhost:8090`.
- Check that PocketBase is actually running: `curl http://localhost:8090/api/health`.

**Issue: "Invalid or expired token" errors on every request**

Cause: The PocketBase admin credentials in `.env` do not match the actual PocketBase admin account.

Solution:
1. Open the PocketBase admin UI and verify you can log in with the credentials in `.env`.
2. If you changed the admin password, update `.env` and restart FastAPI.
3. The PocketBase admin token is cached in memory. Restart FastAPI to clear it: `docker compose restart fastapi`.

**Issue: Gemini LLM calls fail with authentication errors**

Cause: Missing or invalid GCP credentials.

Solution:
1. Verify the service account key file exists at the path specified by `GOOGLE_APPLICATION_CREDENTIALS`.
2. In Docker, this path should be inside the container: `/app/credentials/service-account.json`. The `docker-compose.yml` mounts `./credentials` to `/app/credentials`.
3. Verify the service account has the `Vertex AI User` role.
4. Verify the `GCP_PROJECT_ID` is correct and the Vertex AI API is enabled.

**Issue: Caddy fails to obtain a TLS certificate**

Cause: DNS not pointing to the VM, or ports 80/443 blocked.

Solution:
1. Verify DNS: `dig +short chat.yourdomain.com` should return the VM's IP.
2. Verify firewall: The VM must accept inbound traffic on ports 80 and 443. Check GCP firewall rules.
3. Check Caddy logs: `docker compose logs caddy`.
4. Ensure the `DOMAIN` env var matches your actual domain exactly.

**Issue: PocketBase migration fails**

Cause: Corrupted data or schema conflicts.

Solution:
1. Check PocketBase logs: `docker compose logs pocketbase`.
2. If starting fresh, delete the PocketBase data volume: `docker compose down -v` (warning: this deletes all data).
3. Restart: `docker compose up -d --build`.

**Issue: Chat responses are slow**

Cause: Cold start of Vertex AI models, or retrieval backend latency.

Solution:
1. The first request after startup initializes the Vertex AI SDK (`vertexai.init()`). Subsequent requests reuse the initialization.
2. Retriever instances are cached in memory after first use.
3. For Vertex Search, ensure the datastore is in the same region as specified in `GCP_LOCATION`.
4. For Vector Search, ensure the index endpoint is deployed and warmed up.
5. Consider using a faster Gemini model (e.g., `gemini-2.0-flash` instead of larger models).

**Issue: The admin UI shows "403 Forbidden" when loading configs**

Cause: The logged-in user does not have the `superuser` role.

Solution: Open PocketBase admin UI, navigate to the `users` collection, find the user, and set `role` to `superuser`.

**Issue: Email notifications are not being sent**

Cause: SMTP misconfiguration.

Solution:
1. Verify `SMTP_HOST` is not empty.
2. Verify `ERROR_NOTIFY_EMAILS` is not empty.
3. For Gmail, use an App Password (not your regular password) and enable 2FA on the Google account.
4. Check FastAPI logs for "Failed to send error email" messages.
5. Test SMTP connectivity from the VM: `telnet smtp.gmail.com 587`.

### How to Check Service Health

```bash
# FastAPI health
curl http://localhost:8000/api/health
# Expected: {"status": "ok"}

# PocketBase health
curl http://localhost:8090/api/health
# Expected: {"code": 200, "message": "API is healthy."}

# Docker container status
docker compose ps

# FastAPI logs
docker compose logs fastapi --tail 50

# PocketBase logs
docker compose logs pocketbase --tail 50

# Caddy logs
docker compose logs caddy --tail 50
```

### Log Locations

| Service | Docker Location | Description |
|---|---|---|
| FastAPI | `docker compose logs fastapi` | Python logging output, uvicorn access logs, error tracebacks. |
| PocketBase | `docker compose logs pocketbase` | Database operations, migration runs, auth events. |
| Caddy | `docker compose logs caddy` | HTTP request logs, TLS certificate events, proxy errors. |

For bare-metal development, logs go to stdout/stderr in the terminal where you ran `scripts/run_local.sh`.

To increase log verbosity, set `LOG_LEVEL=debug` in `.env`.

---

## 18. Security Considerations

### Secrets Management

The following values in `.env` are sensitive and must be protected:

| Secret | Risk If Exposed |
|---|---|
| `POCKETBASE_ADMIN_EMAIL` / `POCKETBASE_ADMIN_PASSWORD` | Full admin access to all data (users, configs, chat history). |
| `GOOGLE_APPLICATION_CREDENTIALS` (the key file) | Full access to Google Cloud resources within the service account's permissions. |
| `SMTP_PASSWORD` | Ability to send emails from your SMTP account. |

Best practices:
- Never commit `.env` or `credentials/` to Git. The `.gitignore` should exclude both.
- On VMs, restrict file permissions: `chmod 600 .env` and `chmod 600 credentials/service-account.json`.
- Use GCP Secret Manager for production deployments if your organization requires it.
- Rotate the PocketBase admin password periodically.
- Use a dedicated GCP service account with the minimum required roles (do not use a project owner account).

### HTTPS via Caddy

In production, all traffic should go through Caddy on ports 80/443. Caddy automatically:
- Obtains a TLS certificate from Let's Encrypt.
- Redirects HTTP to HTTPS.
- Handles certificate renewal (every 60-90 days).
- Provides OCSP stapling.

Caddy's certificate data is stored in the `caddy_data` Docker volume. Do not delete this volume unless you want Caddy to re-obtain certificates (which has rate limits).

FastAPI and PocketBase are not exposed directly to the internet in the production Docker Compose configuration. They communicate with Caddy over the internal Docker network.

### PocketBase Access Rules

The database access rules provide defense-in-depth:

- **`rag_configs`**: All operations (list, view, create, update, delete) require `@request.auth.role = 'superuser'`. Regular users cannot read or modify configurations even if they somehow obtain the collection endpoint.
- **`chat_history`**: Users can only list and view their own records (`@request.auth.id = user`). Nobody can update records (immutable audit trail). Only superusers can delete records.
- **`users`**: Managed by PocketBase's built-in rules. Users can view and update their own profile.

These rules are enforced at the PocketBase level, independent of the FastAPI auth middleware. Even if someone bypasses FastAPI and hits PocketBase directly, the access rules still apply.

### What NOT to Commit to Git

The following files and directories must never be committed to the repository:

| Path | Contains |
|---|---|
| `.env` | All secrets: database passwords, SMTP credentials, GCP project ID. |
| `credentials/` | GCP service account key file. |
| `pb/pb_data/` | PocketBase SQLite database containing user passwords, chat history, and configurations. |
| `caddy_data/` (if not using volumes) | TLS private keys and certificates. |

Ensure your `.gitignore` includes:
```
.env
credentials/
pb/pb_data/
```

The deploy script (`scripts/deploy.sh`) explicitly excludes these paths when syncing to remote VMs, so they are never overwritten during deployment.

### Additional Security Notes

- **CORS**: The FastAPI CORS middleware is configured with `allow_origins=["*"]`. For production deployments with strict security requirements, consider restricting this to your actual domain.
- **Rate limiting**: The project does not include rate limiting. For public-facing deployments, consider adding a rate limiter (e.g., `slowapi` for FastAPI, or Caddy rate limiting directives).
- **Input validation**: All API inputs are validated by Pydantic models. The `RetrievalBackend` enum restricts backend values to the four valid options. PocketBase field constraints (min/max on numbers, select values) provide an additional validation layer.
- **Error messages**: The error middleware returns a generic "Internal server error" message to clients, never exposing stack traces or internal details. Detailed error information is sent only to configured email recipients.
- **Token handling**: JWTs are never logged. The PocketBase admin token is cached in memory (not on disk). User tokens are validated on every request via PocketBase's auth-refresh endpoint, which also checks for token revocation.