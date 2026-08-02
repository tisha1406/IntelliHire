from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.response import error_response


def add_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        response_data = error_response(
            message=str(exc.detail),
            meta={"path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Extract validation error messages
        errors = exc.errors()
        error_details = []
        for e in errors:
            loc = " -> ".join([str(l) for l in e["loc"]])
            error_details.append(f"{loc}: {e['msg']}")

        response_data = error_response(
            message="Validation Error",
            meta={
                "path": request.url.path,
                "validation_errors": error_details,
            },
        )
        return JSONResponse(
            status_code=422,
            content=response_data.model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # In production, do not leak internal exceptions, but log them
        # We will use logging later. For now, we return a general error.
        response_data = error_response(
            message="Internal Server Error",
            meta={
                "path": request.url.path,
                "details": str(exc), # In dev it's helpful
            },
        )
        return JSONResponse(
            status_code=500,
            content=response_data.model_dump(),
        )
