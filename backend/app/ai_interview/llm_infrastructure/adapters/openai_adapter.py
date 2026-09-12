import os
import json
import logging
import httpx
from typing import Type, TypeVar, Any, Optional
from pydantic import BaseModel

from app.config.settings import settings

from app.ai_interview.llm_infrastructure.interfaces import LLMProvider
from app.ai_interview.llm_infrastructure.exceptions import (
    LLMGenerationError, LLMTransientError, LLMFatalError
)
from app.ai_interview.llm_infrastructure.parsers import StructuredOutputParser

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)

class OpenAICompatibleAdapter(LLMProvider):
    """
    Adapter for OpenAI or OpenAI-compatible APIs (like local vLLM).
    Uses a synchronous HTTP client for now to preserve Phase 1-6 synchronous orchestration.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY or os.environ.get("OPENAI_API_KEY", "dummy_key")
        self.base_url = base_url or ("https://api.groq.com/openai/v1" if self.api_key == settings.GROQ_API_KEY else "https://api.openai.com/v1")
        self.model = model or ("llama-3.1-8b-instant" if self.api_key == settings.GROQ_API_KEY else "gpt-4o-mini")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # In a real environment, use a shared httpx.Client session

    def _call_api(self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: Optional[int], is_json: bool) -> str:
        # Prompt size protection (Part 4 and 15)
        MAX_PROMPT_LENGTH = 20000
        if len(system_prompt) + len(user_prompt) > MAX_PROMPT_LENGTH:
            raise LLMFatalError(f"Prompt length exceeds safety threshold of {MAX_PROMPT_LENGTH} characters.")
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if is_json and "gpt-4" in self.model or "gpt-3.5" in self.model:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                duration_ms = int(response.elapsed.total_seconds() * 1000)
                logger.info(f"LLM Provider [{self.model}] request completed successfully in {duration_ms}ms (Status: {response.status_code})")
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (429, 500, 502, 503, 504):
                logger.warning(f"Transient HTTP {status} from provider {self.base_url}.")
                raise LLMTransientError(f"Transient provider error: {status}") from e
            else:
                logger.error(f"Fatal HTTP {status} from provider {self.base_url}.")
                raise LLMFatalError(f"Fatal provider error: {status}") from e
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout communicating with provider {self.base_url}.")
            raise LLMTransientError(f"Provider timeout") from e
        except httpx.RequestError as e:
            logger.error(f"Network error communicating with provider {self.base_url}.")
            raise LLMTransientError(f"Provider network error") from e
        except (KeyError, IndexError, ValueError) as e:
            raise LLMFatalError(f"Malformed response from provider: {type(e).__name__}") from e

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> T:
        
        # We append a structural instruction to the system prompt to ensure JSON
        json_instruction = f"\n\nYou MUST respond with valid JSON matching this schema: {json.dumps(response_model.model_json_schema())}"
        full_system = system_prompt + json_instruction
        
        raw_text = self._call_api(
            system_prompt=full_system,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            is_json=True
        )
        
        return StructuredOutputParser.parse_and_validate(raw_text, response_model)

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        return self._call_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            is_json=False
        )
