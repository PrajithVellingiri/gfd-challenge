from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    All credentials and URLs are strictly configurable via environment.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Current environment (development, test, production)")
    HOST: str = Field(default="0.0.0.0", description="Host address to bind the API server")
    PORT: int = Field(default=8000, description="Port for the API server")
    ADMIN_API_KEY: Optional[str] = Field(default=None, description="Secret token to protect administrative endpoints")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origin URLs"
    )

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_KEY: Optional[str] = Field(default=None, description="Supabase anon public key")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, description="Supabase service role secret key")

    # Direct Database Connection
    DATABASE_URL: Optional[str] = Field(
        default=None, 
        description="Direct PostgreSQL connection string for migrations and queries"
    )

    # Storage Buckets
    STORAGE_IMAGE_BUCKET: str = Field(default="citizen-images", description="Storage bucket name for uploaded images")
    STORAGE_AUDIO_BUCKET: str = Field(default="citizen-audio", description="Storage bucket name for uploaded audio files")

    # Google Gemini AI Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key for multimodal analysis")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model identifier (e.g. gemini-1.5-flash or gemini-1.5-pro)")

    # Phase 5: Request Intelligence Configuration
    EMBEDDING_PROVIDER: str = Field(default="gemini", description="Embedding provider: 'gemini', 'local', or 'mock'")
    EMBEDDING_MODEL: str = Field(default="models/text-embedding-004", description="Embedding model identifier")
    EMBEDDING_DIMENSION: int = Field(default=768, description="Vector embedding dimension (768 for text-embedding-004)")
    DUPLICATE_SIMILARITY_THRESHOLD: float = Field(default=0.90, description="Cosine similarity threshold for duplicate detection")
    SIMILARITY_THRESHOLD: float = Field(default=0.75, description="Minimum cosine similarity threshold for storing similar relationships")
    TOP_K_SIMILAR_REQUESTS: int = Field(default=10, description="Maximum number of nearest neighbors to retrieve")
    CLUSTER_EPS: float = Field(default=0.35, description="DBSCAN cosine distance eps parameter (distance = 1 - similarity)")
    CLUSTER_MIN_SAMPLES: int = Field(default=2, description="Minimum cluster size for DBSCAN")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["*"]


settings = Settings()
