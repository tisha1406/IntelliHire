from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings

from app.middleware.logging_middleware import LoggingMiddleware

from app.api.admin.companies import router as companies_router
from app.api.admin.strategies import router as strategies_router
from app.api.admin.interview_modes import router as interview_modes_router


# Startup and Shutdown Events
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 IntelliHire Backend Starting...")
    yield
    print("🛑 IntelliHire Backend Shutting Down...")


# Create FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Multilingual Voice Interview Platform",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Later replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.include_router(companies_router)
app.include_router(strategies_router)
app.include_router(interview_modes_router)

# Root Endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to IntelliHire Backend",
        "status": "Running",
        "version": settings.APP_VERSION,
    }
