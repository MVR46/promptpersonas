"""Interface for interacting with Ollama LLM models."""

import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from .config import OLLAMA_BASE_URL, OLLAMA_API_TIMEOUT, ModelConfig


@dataclass
class LLMResponse:
    """Structured response from an LLM."""
    model: str
    response_text: str
    prompt: str
    config: Dict[str, Any]
    timestamp: str
    tokens_generated: Optional[int] = None
    generation_time: Optional[float] = None  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class OllamaInterface:
    """Interface for communicating with Ollama API."""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: int = OLLAMA_API_TIMEOUT):
        """Initialize the Ollama interface.
        
        Args:
            base_url: Base URL for Ollama API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """List available models in Ollama.
        
        Returns:
            List of model names
        
        Raises:
            ConnectionError: If cannot connect to Ollama
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def generate(
        self,
        model: str,
        prompt: str,
        config: ModelConfig,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            model: Name of the model to use
            prompt: The prompt to send to the model
            config: Model configuration parameters
            system_prompt: Optional system prompt to set context
        
        Returns:
            LLMResponse object with the model's response
        
        Raises:
            ConnectionError: If cannot connect to Ollama
            ValueError: If model is not available
        """
        # Prepare the request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": config.to_dict(),
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        # Make the API call
        try:
            start_time = datetime.now()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            end_time = datetime.now()
            response.raise_for_status()
            
            data = response.json()
            generation_time = (end_time - start_time).total_seconds()
            
            return LLMResponse(
                model=model,
                response_text=data.get("response", ""),
                prompt=prompt,
                config=config.to_dict(),
                timestamp=datetime.now().isoformat(),
                tokens_generated=data.get("eval_count"),
                generation_time=generation_time,
            )
            
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to generate response: {e}")
    
    def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama library.
        
        Args:
            model: Name of the model to pull
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=600,  # 10 minutes for model download
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


def construct_persona_prompt(persona_data: Dict[str, Any], question: str) -> tuple[str, str]:
    """Construct a prompt that embeds persona context with a question.
    
    Args:
        persona_data: Dictionary containing persona information
        question: The question to ask
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Build system prompt with persona context
    system_parts = [
        "You are role-playing as a specific person with the following characteristics:",
        "",
        f"Name: {persona_data.get('name', 'Unknown')}",
        "",
    ]
    
    # Add demographics
    if "demographics" in persona_data:
        system_parts.append("Demographics:")
        demo = persona_data["demographics"]
        for key, value in demo.items():
            if isinstance(value, dict):
                continue
            system_parts.append(f"  - {key.replace('_', ' ').title()}: {value}")
        system_parts.append("")
    
    # Add personality
    if "personality" in persona_data:
        system_parts.append("Personality:")
        personality = persona_data["personality"]
        if "traits" in personality:
            system_parts.append(f"  - Traits: {', '.join(personality['traits'])}")
        if "values" in personality:
            system_parts.append(f"  - Values: {', '.join(personality['values'])}")
        system_parts.append("")
    
    # Add shopping behavior
    if "shopping_behavior" in persona_data:
        system_parts.append("Shopping Behavior:")
        shopping = persona_data["shopping_behavior"]
        for key, value in shopping.items():
            if isinstance(value, list):
                system_parts.append(f"  - {key.replace('_', ' ').title()}:")
                for item in value:
                    system_parts.append(f"    • {item}")
            elif not isinstance(value, dict):
                system_parts.append(f"  - {key.replace('_', ' ').title()}: {value}")
        system_parts.append("")
    
    # Add behavioral notes
    if "behavioral_notes" in persona_data:
        system_parts.append("Additional Context:")
        system_parts.append(persona_data["behavioral_notes"])
        system_parts.append("")
    
    system_parts.extend([
        "Respond to the following question as this person would, considering their",
        "values, preferences, and decision-making style. Be authentic and specific.",
        "Explain your reasoning naturally as this person would."
    ])
    
    system_prompt = "\n".join(system_parts)
    
    # User prompt is just the question
    user_prompt = question
    
    return system_prompt, user_prompt

