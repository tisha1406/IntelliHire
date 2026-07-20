from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import settings

client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_db():
    """
    Create MongoDB connection when the application starts.
    """
    global client, database

    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client.get_default_database()

    print("✅ Connected to MongoDB")


async def close_db():
    """
    Close MongoDB connection when the application shuts down.
    """
    global client

    if client:
        client.close()
        print("🔴 MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the active MongoDB database instance.
    """
    if database is None:
        raise RuntimeError("Database is not connected.")

    return database