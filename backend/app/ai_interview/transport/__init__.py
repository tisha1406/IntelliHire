"""
Phase 9 — Interview Transport Layer
====================================
Global registry for the bounded ThreadPoolExecutor used to run synchronous
Phase 1–7 engine operations (including LLM calls) without blocking the
FastAPI asyncio event loop.

Lifecycle:
- set_interview_executor() is called once during FastAPI lifespan startup.
- get_interview_executor() is called by InterviewTransportService.
- The executor is shut down during lifespan teardown.
"""
from __future__ import annotations

import concurrent.futures
from typing import Optional

_interview_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def set_interview_executor(executor: concurrent.futures.ThreadPoolExecutor) -> None:
    """Register the bounded executor created during lifespan startup."""
    global _interview_executor
    _interview_executor = executor


def get_interview_executor() -> concurrent.futures.ThreadPoolExecutor:
    """
    Return the bounded interview executor.

    Raises RuntimeError if called before lifespan startup completes.
    """
    if _interview_executor is None:
        raise RuntimeError(
            "Interview executor has not been initialized. "
            "Ensure set_interview_executor() is called during FastAPI lifespan startup."
        )
    return _interview_executor
