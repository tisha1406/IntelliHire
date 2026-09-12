import json
import re
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError

from app.ai_interview.llm_infrastructure.exceptions import LLMValidationError

T = TypeVar('T', bound=BaseModel)

class StructuredOutputParser:
    """
    Handles robust extraction of JSON from raw LLM text and Pydantic validation.
    """
    
    @staticmethod
    def extract_json(raw_text: str) -> str:
        """
        Extracts JSON from markdown code blocks or raw text.
        """
        if len(raw_text) > 50000:
            raise LLMValidationError(f"Response too large to parse ({len(raw_text)} chars).")
            
        text = raw_text.strip()
        
        # Look for markdown JSON blocks
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            
        # Fallback: find first { or [ and last } or ]
        start_idx = -1
        end_idx = -1
        
        # Determine if it's an object or array
        obj_start = text.find('{')
        arr_start = text.find('[')
        
        if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
            start_idx = obj_start
            end_idx = text.rfind('}')
        elif arr_start != -1:
            start_idx = arr_start
            end_idx = text.rfind(']')
            
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            text = text[start_idx:end_idx+1]
            
        return text

    @staticmethod
    def repair_json(json_str: str) -> str:
        """
        Performs basic repairs like removing trailing commas.
        """
        # Simple regex to remove trailing commas before closing braces/brackets
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        return json_str

    @classmethod
    def parse_and_validate(cls, raw_text: str, response_model: Type[T]) -> T:
        """
        Extracts, parses, and validates the raw text into the requested Pydantic model.
        """
        extracted = cls.extract_json(raw_text)
        repaired = cls.repair_json(extracted)
        
        try:
            parsed_dict = json.loads(repaired)
        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Failed to decode JSON: {e}\nRaw extracted:\n{repaired}") from e
            
        try:
            return response_model.model_validate(parsed_dict)
        except ValidationError as e:
            raise LLMValidationError(f"Pydantic validation failed: {e}\nParsed dict:\n{parsed_dict}") from e
