from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.db.mongo import connect_db, close_db

from app.middleware.logging_middleware import LoggingMiddleware

from app.api.admin.companies import router as companies_router
from app.api.admin.strategies import router as strategies_router
from app.api.admin.interview_modes import router as interview_modes_router
from app.api.company.campaigns import router as campaigns_router

from app.db.indexes import create_indexes


# Startup and Shutdown Events
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 IntelliHire Backend Starting...")

    # Connect to MongoDB
    await connect_db()

    await create_indexes()

    yield

    # Close MongoDB Connection
    await close_db()

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

# Register Routers
app.include_router(companies_router)
app.include_router(strategies_router)
app.include_router(interview_modes_router)
app.include_router(campaigns_router)


# Root Endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to IntelliHire Backend",
        "status": "Running",
        "version": settings.APP_VERSION,
    }