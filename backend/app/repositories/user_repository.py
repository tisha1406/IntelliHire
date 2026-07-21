from datetime import UTC, datetime

from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    Repository for User collection.
    Provides user-specific database operations.
    """

    def __init__(self):
        super().__init__("users")

    async def get_by_email(self, email: str):
        """
        Fetch a user by email address.
        """
        return await self.get_one(
            {"email": email}
        )

    async def get_by_refresh_token(self, refresh_token_hash: str):
        """
        Fetch a user using the stored refresh token hash.
        """
        return await self.get_one(
            {"refresh_token_hash": refresh_token_hash}
        )

    async def store_refresh_token(
        self,
        user_id: str,
        refresh_token_hash: str,
    ) -> bool:
        """
        Save or update the user's refresh token hash.
        """
        return await self.update(
            user_id,
            {
                "refresh_token_hash": refresh_token_hash,
                "updated_at": datetime.now(UTC),
            },
        )

    async def clear_refresh_token(
        self,
        user_id: str,
    ) -> bool:
        """
        Remove the stored refresh token during logout.
        """
        return await self.update(
            user_id,
            {
                "refresh_token_hash": None,
                "updated_at": datetime.now(UTC),
            },
        )

    async def update_last_login(
        self,
        user_id: str,
    ) -> bool:
        """
        Update the user's last successful login timestamp.
        """
        return await self.update(
            user_id,
            {
                "last_login": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )