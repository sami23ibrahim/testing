from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum


class RetrievalBackend(str, Enum):
    NONE = "none"
    RAG_STORE = "rag_store"
    VERTEX_SEARCH = "vertex_search"
    VECTOR_SEARCH = "vector_search"


class Settings(BaseSettings):
    # GCP (optional — leave blank for local-only / direct Gemini mode)
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    google_application_credentials: str = ""

    # Default retrieval ("none" = direct Gemini, no retrieval)
    default_retrieval_backend: RetrievalBackend = RetrievalBackend.NONE

    # Vertex RAG Store
    rag_corpus_name: str = ""

    # Vertex AI Search
    vertex_search_datastore: str = ""
    vertex_search_serving_config: str = ""

    # Vector Search
    vector_search_index_endpoint: str = ""
    vector_search_deployed_index_id: str = ""
    embedding_model: str = "text-embedding-005"

    # LLM
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.3
    llm_max_output_tokens: int = 2048

    # PocketBase
    pocketbase_url: str = "http://pocketbase:8090"
    pocketbase_admin_email: str = ""
    pocketbase_admin_password: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 2
    log_level: str = "info"

    # Caddy
    domain: str = "localhost"

    # Branding (customizable per clone)
    bot_name: str = "Chat Assistant"
    bot_icon_url: str = ""
    welcome_title: str = "How can I help you?"
    welcome_subtitle: str = "Ask me anything."
    powered_by_text: str = ""

    # Content moderation
    moderation_enabled: bool = True
    moderation_custom_blocked: str = ""  # comma-separated extra words to block

    # Error email notifications
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True
    error_notify_emails: str = ""  # comma-separated superuser emails

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
