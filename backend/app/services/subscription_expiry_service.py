from datetime import datetime, UTC, timedelta
from app.repositories.company_repository import CompanyRepository
from app.services.notification_service import NotificationService
from app.db.models import CompanySubscription

class SubscriptionExpiryService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.notification_service = NotificationService()

    async def check_expiring_subscriptions(self):
        """
        Background task to find subscriptions nearing expiry and trigger notifications.
        Typically run once daily.
        """
        now = datetime.now(UTC)
        thresholds = [30, 15, 7, 3, 1, 0]

        # Fetch all active companies
        query = {"subscription.status": "active", "subscription.expiry_date": {"$ne": None}}
        companies = await self.company_repo.get_many(query)

        for company in companies:
            sub = company.get("subscription", {})
            expiry_date = sub.get("expiry_date")
            if not expiry_date:
                continue

            # Handle expiry_date if it's stored as a string or datetime
            if isinstance(expiry_date, str):
                try:
                    expiry_date = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
                except ValueError:
                    continue

            # Ensure expiry_date is timezone aware
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=UTC)

            days_remaining = (expiry_date - now).days

            if days_remaining < 0:
                await self._expire_subscription(str(company["_id"]))
            elif days_remaining in thresholds:
                await self._notify_expiry(str(company["_id"]), days_remaining)

    async def _expire_subscription(self, company_id: str):
        # Update subscription status to expired
        update_data = {"subscription.status": "expired"}
        await self.company_repo.update(company_id, update_data)
        
        # Notify company
        title = "Subscription Expired"
        msg = "Your IntelliHire subscription has expired. Please renew to regain access to premium features."
        
        await self._send_if_not_duplicate(company_id, title, msg)

    async def _notify_expiry(self, company_id: str, days: int):
        if days == 0:
            msg = "Your IntelliHire subscription expires today!"
        else:
            msg = f"Your IntelliHire subscription will expire in {days} days."
            
        title = "Subscription Expiring Soon"
        await self._send_if_not_duplicate(company_id, title, msg)
        
    async def _send_if_not_duplicate(self, company_id: str, title: str, msg: str):
        from app.db.mongo import get_database
        from bson import ObjectId
        db = get_database()
        
        # Check if we already sent this exact message to this company recently
        # We check within the last 24 hours to prevent duplicate spam
        yesterday = datetime.now(UTC) - timedelta(hours=24)
        
        existing = await db.notifications.find_one({
            "recipient_id": ObjectId(company_id),
            "title": title,
            "message": msg,
            "created_at": {"$gte": yesterday}
        })
        
        if not existing:
            await self.notification_service.create_notification(
                admin_id="system",
                target=company_id,
                notification_type="billing",
                title=title,
                message=msg
            )
