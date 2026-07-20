import json
import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


# Configure Logger
logger = logging.getLogger("intellihire")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))

logger.addHandler(handler)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging every request and response.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = round((time.time() - start_time) * 1000, 2)

        log = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": process_time,
            "client": request.client.host if request.client else None,
        }

        logger.info(json.dumps(log))

        return response