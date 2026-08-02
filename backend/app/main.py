from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.db.mongo import connect_db, close_db
from app.db.indexes import create_indexes

from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.exception_handlers import add_exception_handlers

# ===========================
# Admin APIs
# ===========================
from app.api.admin.companies import router as companies_router
from app.api.admin.strategies import router as strategies_router
from app.api.admin.interview_modes import router as interview_modes_router
from app.api.admin.analytics import router as analytics_router
from app.api.admin.settings import router as settings_router
from app.api.admin.system import router as system_router
from app.api.admin.recruiters import router as recruiters_router
from app.api.admin.candidates import router as candidates_admin_router
from app.api.admin.interviews import router as interviews_admin_router
from app.api.admin.ai_center import router as ai_center_router
from app.api.admin.users import router as users_admin_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.admin.notifications import router as notifications_router
from app.api.admin.profile import router as profile_router
from app.api.admin.reports import router as reports_router
from app.api.admin.ai_reports import router as ai_reports_router
from app.api.admin.storage import router as storage_router

# ===========================
# Company APIs
# ===========================
from app.api.company.campaigns import router as campaigns_router
from app.api.company.candidates import router as company_candidates_router
from app.api.company.jobs import router as jobs_router
from app.api.company.reports import router as company_reports_router
from app.api.company.exports import router as exports_router
from app.api.company.analytics import router as company_analytics_router
from app.api.company.team import router as team_router
from app.api.company.profile import router as company_profile_router

# ===========================
# Authentication
# ===========================
from app.api.auth import router as auth_router

# ===========================
# Candidate APIs
# ===========================
from app.api.candidates import router as candidates_router
from app.api.candidate_portal import router as candidate_portal_router
from app.api.resume import router as resume_router
from app.api.interview import router as interview_router

# ===========================
# WebSocket APIs
# ===========================
from app.api.ws import router as ws_router


# ==========================================================
# Startup / Shutdown
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 IntelliHire Backend Starting...")

    await connect_db()
    await create_indexes()

    yield

    await close_db()

    print("🛑 IntelliHire Backend Shutting Down...")


# ==========================================================
# FastAPI App
# ==========================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Multilingual Voice Interview Platform",
    lifespan=lifespan,
)

# ==========================================================
# Middleware
# ==========================================================
add_exception_handlers(app)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Register Routers
# ==========================================================

# ---------- Admin ----------
app.include_router(companies_router)
app.include_router(strategies_router)
app.include_router(interview_modes_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(system_router)
app.include_router(recruiters_router)
app.include_router(candidates_admin_router)
app.include_router(interviews_admin_router)
app.include_router(ai_center_router)
app.include_router(users_admin_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(profile_router)
app.include_router(storage_router)
app.include_router(reports_router)
app.include_router(ai_reports_router)

# ---------- Company ----------
app.include_router(campaigns_router)
app.include_router(jobs_router)
app.include_router(company_candidates_router)
app.include_router(company_reports_router)
app.include_router(exports_router)
app.include_router(company_analytics_router)
app.include_router(team_router)
app.include_router(company_profile_router)

# ---------- Authentication ----------
app.include_router(auth_router)

# ---------- Candidate ----------
app.include_router(candidates_router)
app.include_router(candidate_portal_router)
app.include_router(resume_router)
app.include_router(interview_router)

# ---------- WebSockets ----------
app.include_router(ws_router)

# ==========================================================
# Root Endpoint
# ==========================================================
@app.get("/")
async def root():
    return {
        "message": "Welcome to IntelliHire Backend",
        "status": "Running",
        "version": settings.APP_VERSION,
    }