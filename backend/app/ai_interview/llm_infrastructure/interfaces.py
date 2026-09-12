from typing import Protocol, TypeVar, Type, Any, Dict, Optional
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMProvider(Protocol):
    """
    Protocol defining the contract for any LLM Provider Adapter.
    This abstraction ensures the deterministic engines never couple 
    to specific OpenAI, Gemini, or local models.
    """
    
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> T:
        """
        Generates a strictly typed Pydantic object from the LLM.
        The adapter is responsible for handling raw string/JSON extraction
        and enforcing schema validation before returning.
        
        Args:
            system_prompt: Core instruction set and constraints.
            user_prompt: The specific request context.
            response_model: The Pydantic BaseModel class to return.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens for the generation.
            
        Returns:
            An instance of response_model populated by the LLM.
            
        Raises:
            LLMGenerationError: On provider failure (network, auth, timeout).
            LLMValidationError: If the output cannot be parsed into response_model.
        """
        ...
        
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Generates plain text. Useful for rationale or non-structured tasks.
        """
        ...
