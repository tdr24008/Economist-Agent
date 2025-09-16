"""Model provider configuration for Hybrid RAG Agent integrating with existing infrastructure."""

from pydantic_ai.models.test import TestModel
from settings import load_settings
import warnings
import os

# Import from existing infrastructure
from utils.providers import get_llm_model as infra_get_llm_model, get_embedding_client, get_embedding_model

def get_llm_model():
    """Get configured LLM model using existing infrastructure with fallback to TestModel."""
    settings = load_settings()
    
    # Use TestModel in mock mode or when API key is missing
    if settings.should_use_mocks() or not settings.llm_api_key:
        warnings.warn("Using TestModel for development/testing", UserWarning)
        return TestModel()
    
    try:
        # Use the existing infrastructure's model provider
        return infra_get_llm_model()
    except Exception as e:
        warnings.warn(f"Failed to initialize model from infrastructure: {e}. Using TestModel", UserWarning)
        return TestModel()

# Re-export functions from existing infrastructure for convenience
__all__ = ['get_llm_model', 'get_embedding_client', 'get_embedding_model']