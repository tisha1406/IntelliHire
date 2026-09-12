import asyncio
import logging
from typing import Awaitable, Callable, TypeVar
from functools import wraps
from app.ai_interview.speech_infrastructure.exceptions import STTTransientError, STTFatalError

logger = logging.getLogger(__name__)

T = TypeVar("T")

class STTResiliencePolicy:
    """
    Implements bounded retries for transient Speech-to-Text provider failures.
    Ensures that infinite retries are impossible and failures surface safely.
    """
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    async def execute(self, operation: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except STTTransientError as e:
                if attempt == self.max_attempts:
                    logger.error(f"STT Resilience: Transient error persisted after {attempt} attempts: {e}")
                    raise
                
                delay = self.base_delay * (2 ** (attempt - 1))
                logger.warning(f"STT Resilience: Transient failure (attempt {attempt}/{self.max_attempts}). Retrying in {delay}s. Reason: {e}")
                await asyncio.sleep(delay)
            except STTFatalError:
                # Never retry fatal errors
                raise

class TTSResiliencePolicy:
    """
    Implements bounded retries for transient Text-to-Speech provider failures.
    Ensures that infinite retries are impossible and failures surface safely.
    """
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    async def execute(self, operation: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                # Import TTS exceptions locally to avoid circular dependencies if any,
                # or just use them from the module if imported globally
                from app.ai_interview.speech_infrastructure.exceptions import TTSTransientError, TTSFatalError
                
                if isinstance(e, TTSTransientError):
                    if attempt == self.max_attempts:
                        logger.error(f"TTS Resilience: Transient error persisted after {attempt} attempts: {e}")
                        raise
                    
                    delay = self.base_delay * (2 ** (attempt - 1))
                    logger.warning(f"TTS Resilience: Transient failure (attempt {attempt}/{self.max_attempts}). Retrying in {delay}s. Reason: {e}")
                    await asyncio.sleep(delay)
                elif isinstance(e, TTSFatalError):
                    # Never retry fatal errors
                    raise
                else:
                    raise
