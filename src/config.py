"""Configuration management for the LLM testing pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    name: str
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    num_predict: int = 500  # max tokens to generate
    repeat_penalty: float = 1.1
    context_window: Optional[int] = None  # uses model default if None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for API calls."""
        config = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_predict": self.num_predict,
            "repeat_penalty": self.repeat_penalty,
        }
        if self.context_window:
            config["num_ctx"] = self.context_window
        return config


# Default model configurations optimized for different use cases
DEFAULT_CONFIGS = {
    "balanced": ModelConfig(
        name="balanced",
        temperature=0.7,
        top_p=0.9,
    ),
    "creative": ModelConfig(
        name="creative",
        temperature=0.9,
        top_p=0.95,
        repeat_penalty=1.05,
    ),
    "precise": ModelConfig(
        name="precise",
        temperature=0.3,
        top_p=0.8,
        repeat_penalty=1.2,
    ),
    "deterministic": ModelConfig(
        name="deterministic",
        temperature=0.1,
        top_p=0.5,
        repeat_penalty=1.3,
    ),
}


# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_TIMEOUT = 120  # seconds

# Popular models for M1 Mac
RECOMMENDED_MODELS = [
    "llama3.1:8b",
    "llama3:8b", 
    "mistral:7b",
    "phi3:medium",
    "gemma2:9b",
    "qwen2.5:7b",
]

# Directories
PERSONAS_DIR = "personas"
QUESTIONS_DIR = "questions"
RESULTS_DIR = "results"

