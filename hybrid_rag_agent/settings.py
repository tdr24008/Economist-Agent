"""Configuration management for Hybrid RAG Agent."""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv
from typing import Optional
import warnings

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Weaviate Configuration (Primary Vector Storage)
    weaviate_url: str = Field(
        default="http://localhost:8080",
        description="Weaviate instance URL"
    )
    weaviate_api_key: Optional[str] = Field(
        default=None,
        description="Weaviate API key for cloud instances"
    )
    
    # LLM Configuration
    llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for the LLM provider"
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="Model name to use"
    )
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the LLM API"
    )
    
    # Embedding Configuration
    embedding_api_key: Optional[str] = Field(
        default=None,
        description="API key for embedding service"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model to use"
    )
    
    # Neo4j Configuration (Knowledge Graph)
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: Optional[str] = Field(
        default=None,
        description="Neo4j password"
    )

    # Routing Configuration
    routing_mode: str = Field(
        default="auto",
        description="Search routing mode: auto, manual, weaviate_only, neo4j_only"
    )
    routing_threshold: float = Field(
        default=0.4,
        description="Confidence threshold for routing decisions"
    )
    
    def is_production_ready(self) -> bool:
        """Check if all required credentials are present for production use."""
        required = [
            self.llm_api_key,
            self.embedding_api_key
        ]
        return all(required)
    
    def should_use_mocks(self) -> bool:
        """Determine if mock mode should be enabled."""
        if not self.is_production_ready():
            warnings.warn(
                "Missing required credentials. Running in MOCK MODE. "
                "Set LLM_API_KEY and EMBEDDING_API_KEY for production use.",
                UserWarning
            )
            return True
        return False

def load_settings() -> Settings:
    """Load settings with proper error handling and environment loading."""
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        settings = Settings()
        if settings.should_use_mocks():
            print("🔧 Running in MOCK MODE - no real database connections")
        return settings
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        warnings.warn(error_msg)
        # Return settings with defaults for mock mode
        return Settings()