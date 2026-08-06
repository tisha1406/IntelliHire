from typing import Optional

from bson import ObjectId

from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository):

    def __init__(self):
        super().__init__("companies")

    # ==========================================================
    # Get Company by ID
    # ==========================================================

    async def get_by_id(
        self,
        document_id: str,
        include_deleted: bool = False,
    ) -> Optional[dict]:

        query = {
            "_id": ObjectId(document_id)
        }

        if not include_deleted:
            query["deleted_at"] = None

        return await self.collection.find_one(query)

    # ==========================================================
    # Get Multiple Companies
    # ==========================================================

    async def get_many(
        self,
        query: dict = {},
        limit: int = 100,
        skip: int = 0,
        include_deleted: bool = False,
    ) -> list[dict]:

        final_query = query.copy()

        if not include_deleted:
            final_query["deleted_at"] = None

        cursor = (
            self.collection
            .find(final_query)
            .skip(skip)
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    # ==========================================================
    # Count Companies
    # ==========================================================

    async def count(
        self,
        query: dict = {},
        include_deleted: bool = False,
    ) -> int:

        final_query = query.copy()

        if not include_deleted:
            final_query["deleted_at"] = None

        return await self.collection.count_documents(
            final_query
        )

    # ==========================================================
    # Lookup by Contact Email
    # Enterprise Schema:
    # general.contact_email
    # ==========================================================

    async def get_by_email(
        self,
        email: str,
        include_deleted: bool = False,
    ):

        query = {
            "general.contact_email": email
        }

        if not include_deleted:
            query["deleted_at"] = None

        return await self.collection.find_one(query)

    # ==========================================================
    # Active Companies
    # Enterprise Schema:
    # subscription.status
    # ==========================================================

    async def get_active_companies(self):

        return await self.get_many(
            {
                "subscription.status": "active"
            },
            include_deleted=False,
        )

    # ==========================================================
    # Generic List
    # (Added from Selin's repository)
    # ==========================================================

    async def list(
        self,
        filters: dict | None = None,
        limit: int = 100,
        skip: int = 0,
        include_deleted: bool = False,
    ):

        return await self.get_many(
            query=filters or {},
            limit=limit,
            skip=skip,
            include_deleted=include_deleted,
        )

    # ==========================================================
    # Authentication Support
    # ==========================================================

    async def store_refresh_token(
        self,
        company_id: str,
        refresh_token_hash: str,
    ) -> bool:
        from datetime import UTC, datetime
        return await self.update(
            company_id,
            {
                "refresh_token_hash": refresh_token_hash,
                "updated_at": datetime.now(UTC),
            },
        )

    async def clear_refresh_token(
        self,
        company_id: str,
    ) -> bool:
        from datetime import UTC, datetime
        return await self.update(
            company_id,
            {
                "refresh_token_hash": None,
                "updated_at": datetime.now(UTC),
            },
        )

    async def update_last_login(
        self,
        company_id: str,
    ) -> bool:
        from datetime import UTC, datetime
        return await self.update(
            company_id,
            {
                "last_login": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )