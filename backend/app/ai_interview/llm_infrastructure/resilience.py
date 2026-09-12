import time
import logging
from typing import Callable, TypeVar, Any

from app.ai_interview.llm_infrastructure.exceptions import (
    LLMGenerationError, LLMValidationError, LLMTransientError, LLMFatalError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ResiliencePolicy:
    """
    Handles simple retry logic for LLM operations.
    In Phase 8/9, this could be expanded to use tenacity or circuit breaker patterns.
    """
    
    @staticmethod
    def execute_with_retry(
        func: Callable[..., T],
        max_attempts: int = 3,
        base_delay_seconds: float = 1.0,
        max_operation_time_seconds: float = 60.0,
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Executes a callable with linear/exponential backoff.
        
        Args:
            func: The function to execute.
            max_attempts: Total attempts allowed (including the first).
            base_delay_seconds: Base delay between retries.
            max_operation_time_seconds: Maximum total allowed time across all retries.
        """
        last_exception = None
        start_time = time.time()
        
        for attempt in range(1, max_attempts + 1):
            if time.time() - start_time >= max_operation_time_seconds:
                logger.error(f"Operation time budget of {max_operation_time_seconds}s exceeded before attempt {attempt}.")
                raise TimeoutError(f"Total operation timeout exceeded: {max_operation_time_seconds}s")
                
            try:
                return func(*args, **kwargs)
            except LLMFatalError as e:
                logger.error(f"Fatal error encountered. Aborting retries: {e}")
                raise
            except (LLMTransientError, LLMValidationError) as e:
                last_exception = e
                logger.warning(f"LLM operation failed (Attempt {attempt}/{max_attempts}): {e}")
                
                if attempt < max_attempts:
                    delay = base_delay_seconds * attempt
                    if time.time() - start_time + delay >= max_operation_time_seconds:
                        logger.error(f"Next retry delay ({delay}s) would exceed max operation time budget ({max_operation_time_seconds}s). Aborting retries.")
                        break
                    
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
        raise last_exception or RuntimeError("execute_with_retry failed unexpectedly without an exception")
