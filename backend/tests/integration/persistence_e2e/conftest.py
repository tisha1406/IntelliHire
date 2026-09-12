import pytest
import pytest_asyncio
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.ai_interview.persistence.repository import InterviewSessionRepository

# Use a specific database for integration tests to avoid corrupting dev data
TEST_DB_NAME = "intellihire_e2e_integration_test_db"

@pytest_asyncio.fixture
async def mongo_client():
    """Provides a real Motor client for the entire test session."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    # Ensure we start with a clean slate
    await client.drop_database(TEST_DB_NAME)
    yield client
    # Cleanup after test session
    await client.drop_database(TEST_DB_NAME)
    client.close()

@pytest_asyncio.fixture
async def real_db(mongo_client):
    """Provides the testing database instance and cleans it before each test."""
    db = mongo_client[TEST_DB_NAME]
    # Clean collections before each test for isolation
    await db.interview_sessions.delete_many({})
    yield db

@pytest_asyncio.fixture
async def real_repo(real_db):
    """Provides a real InterviewSessionRepository connected to the test DB."""
    # We inject the collection explicitly
    repo = InterviewSessionRepository(collection=real_db["interview_sessions"])
    return repo
