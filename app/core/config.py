"""Application configuration.

We use Pydantic Settings to read configuration from environment variables
(and from a local `.env` file in development). This keeps secrets OUT of the
codebase and lets the same code run in dev/staging/prod with different config.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Tell Pydantic to load variables from a `.env` file if present.
    # `extra="ignore"` means unknown env vars won't crash the app.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required: the database connection string. If it's missing, the app
    # refuses to start (fail fast > fail mysteriously later).
    DATABASE_URL: str

    # Optional with a default.
    APP_NAME: str = "Enterprise AI Incident Manager"

    # --- Security / JWT settings (Phase 8) ---
    # SECRET_KEY signs the JWTs. MUST be long, random, and secret in production.
    # If it leaks, anyone can forge valid tokens. Override it via .env.
    SECRET_KEY: str = "dev-only-insecure-change-me"
    ALGORITHM: str = "HS256"  # HMAC + SHA-256 signing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- AI / LLM settings (Phase 11) ---
    # The local Ollama model. Swap this one line to change models/providers.
    LLM_MODEL: str = "llama3.1:8b"
    LLM_TEMPERATURE: float = 0.2  # low = focused/deterministic (good for analysis)
    OLLAMA_HOST: str = "http://localhost:11434"

    # --- RAG (Phase 15) ---
    EMBEDDING_MODEL: str = "nomic-embed-text"  # local Ollama embedding model
    CHROMA_DIR: str = "./chroma_db"            # where the vector store persists


# A single, importable settings instance used across the app.
settings = Settings()
