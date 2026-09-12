import pytest
import time
from app.ai_interview.llm_infrastructure.resilience import ResiliencePolicy
from app.ai_interview.llm_infrastructure.exceptions import LLMTransientError

def test_operation_timeout_exhaustion_stops_retries():
    # Simulate a func that throws transient errors and takes no time
    def failing_func():
        raise LLMTransientError("Simulated timeout")
        
    start = time.time()
    
    with pytest.raises(LLMTransientError, match="Simulated timeout"):
        # We give it a max operation time of 1 second, but base delay of 0.6 seconds.
        # Attempt 1: fails, delay = 0.6s
        # Attempt 2: fails, delay = 1.2s
        # The sum of delays is 1.8s. The resilience policy should abort before waiting 1.2s!
        ResiliencePolicy.execute_with_retry(
            failing_func,
            max_attempts=3,
            base_delay_seconds=0.6,
            max_operation_time_seconds=1.0
        )
        
    duration = time.time() - start
    
    # Duration should be bounded tightly around 0.6s, well under the 1.8s it would have taken
    assert duration < 1.0
