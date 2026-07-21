from fastapi import HTTPException, status

from app.auth.jwt_handler import (
    verify_password,
    create_access_token,
    create_refresh_token,
)

from app.repositories.user_repository import UserRepository


class AuthService:

    def __init__(self):
        self.user_repo = UserRepository()

    async def login(
        self,
        email: str,
        password: str,
    ):

        user = await self.user_repo.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            password,
            user["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(
            user_id=str(user["_id"]),
            role=user["role"],
            company_id=user.get("company_id"),
        )

        refresh_token = create_refresh_token()

        await self.user_repo.update_last_login(
            str(user["_id"])
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user["role"],
            "company_id": user.get("company_id"),
        }