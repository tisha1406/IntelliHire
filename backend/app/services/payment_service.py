import uuid
from datetime import datetime, UTC
from app.db.mongo import get_database
from app.db.models import Payment

class PaymentProvider:
    async def create_order(self, amount: float, currency: str, metadata: dict) -> dict:
        raise NotImplementedError
    
    async def verify_payment(self, payment_id: str, order_id: str, signature: str = None) -> bool:
        raise NotImplementedError


class IntelliHirePaymentProvider(PaymentProvider):
    async def create_order(self, amount: float, currency: str, metadata: dict) -> dict:
        # Generate internal order ID
        random_hex = uuid.uuid4().hex[:8].upper()
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        order_id = metadata.get("receipt", f"INTL-ORD-{date_str}-{random_hex}")
        payment_session_id = f"INTL-SESS-{uuid.uuid4().hex}"
        
        return {
            "id": order_id,
            "payment_session_id": payment_session_id,
            "amount": float(amount),
            "currency": currency,
            "status": "ACTIVE"
        }

    async def verify_payment(self, payment_id: str, order_id: str, signature: str = None) -> bool:
        # Internal verification simulates a direct database check
        # We assume if this function is called, the payment was processed successfully on the simulated frontend
        # and we verify it against the payment order we have stored in DB in the PaymentService layer.
        # So we just return True for the provider's part since it's an internal simulator.
        return True


class PaymentService:
    def __init__(self):
        self.provider = IntelliHirePaymentProvider()

    async def create_payment_order(self, company_id: str, amount: float, currency: str, metadata: dict) -> dict:
        order = await self.provider.create_order(amount, currency, metadata)
        
        db = get_database()
        payment_type = metadata.get("payment_type", "adjustment")
        provider_name = "intellihire"
        
        payment = Payment(
            company_id=company_id,
            payment_type=payment_type,
            provider=provider_name,
            order_id=order.get("id"),
            amount=amount,
            currency=currency,
            status="pending"
        )
        await db.payments.insert_one(payment.model_dump(by_alias=True, exclude_none=True))
        
        return order

    async def verify_payment(self, company_id: str, payment_id: str, order_id: str, signature: str = None) -> bool:
        db = get_database()
        
        existing = await db.payments.find_one({"order_id": order_id})
        if not existing:
            return False
            
        if str(existing.get("company_id")) != str(company_id):
            return False
            
        if existing.get("status") == "verified" or existing.get("status") == "success":
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Order already paid")
            
        is_valid = await self.provider.verify_payment(payment_id, order_id, signature)
        
        if is_valid:
            # Generate a simulated transaction ID if a payment ID wasn't provided
            if not payment_id:
                payment_id = f"INTL-PAY-{uuid.uuid4().hex[:10].upper()}"
                
            await db.payments.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": "success",
                        "payment_id": payment_id,
                        "updated_at": datetime.now(UTC),
                        "verified_at": datetime.now(UTC)
                    }
                }
            )
            return True
            
        return False
