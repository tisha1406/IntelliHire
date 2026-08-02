from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import settings


client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_db():
    """
    Initialize MongoDB connection during application startup.

    Uses the database specified in settings.DATABASE_NAME to ensure
    consistent behaviour across development, testing, and production.
    """
    global client, database

    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.DATABASE_NAME]

    print("[OK] Connected to MongoDB")


async def close_db():
    """
    Close MongoDB connection during application shutdown.
    """
    global client

    if client is not None:
        client.close()
        print("[INFO] MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the active MongoDB database instance.

    Raises:
        RuntimeError: If the database connection has not been initialized.
    """
    if database is None:
        raise RuntimeError(
            "MongoDB connection has not been initialized. "
            "Call connect_db() during application startup."
        )

    return database