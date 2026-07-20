from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class SessionNotFoundException(Exception):
    """Raised when an interview session cannot be found."""
    pass


class LLMUnavailableException(Exception):
    """Raised when the AI model is unavailable."""
    pass


class PermissionDeniedException(Exception):
    """Raised when a user is not authorized."""
    pass



async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors()
        }
    )

async def permission_exception_handler(
    request: Request,
    exc: PermissionDeniedException
):
    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "error": "Permission Denied"
        }
    )

async def session_exception_handler(
    request: Request,
    exc: SessionNotFoundException
):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Interview Session Not Found"
        }
    )

async def llm_exception_handler(
    request: Request,
    exc: LLMUnavailableException
):
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": "LLM Service Unavailable"
        }
    )

async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error"
        }
    )

def register_exception_handlers(app: FastAPI):

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )

    app.add_exception_handler(
        PermissionDeniedException,
        permission_exception_handler
    )

    app.add_exception_handler(
        SessionNotFoundException,
        session_exception_handler
    )

    app.add_exception_handler(
        LLMUnavailableException,
        llm_exception_handler
    )

    app.add_exception_handler(
        Exception,
        generic_exception_handler
    )