import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pymongo.asynchronous.collection import AsyncCollection
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.persistence.exceptions import (
    OptimisticConcurrencyError,
    SessionNotFoundError,
    IdempotencyConflictError,
    FencingTokenError,
    ClaimAlreadyHeldError
)
from app.ai_interview.persistence.validator import SessionPersistenceValidator

logger = logging.getLogger(__name__)

class InterviewSessionRepository:
    """
    Repository for InterviewSessionSchema.
    Implements OCC, conditional updates, and domain mapping.
    Uses PyMongo's native Async API (v4.4+).
    """
    
    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    def _map_to_domain(self, doc: Dict[str, Any]) -> InterviewSessionSchema:
        """Map BSON back to Pydantic domain, omitting _id."""
        if "_id" in doc:
            del doc["_id"]
        # In a real environment, we would handle schema_version migrations here (lazy migration).
        # We assume the data perfectly maps to our current InterviewSessionSchema.
        return InterviewSessionSchema.model_validate(doc)
        
    def _map_to_bson(self, session: InterviewSessionSchema) -> Dict[str, Any]:
        """Serialize Pydantic domain to BSON-compatible dict."""
        # By default model_dump returns dict, we need to ensure enums are values, etc.
        return session.model_dump(mode="json")

    async def get_by_id(self, session_id: str) -> InterviewSessionSchema:
        doc = await self.collection.find_one({"session_id": session_id})
        if not doc:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        return self._map_to_domain(doc)

    async def find_active_session(self, candidate_id: str, campaign_id: str) -> Optional[InterviewSessionSchema]:
        """Finds an existing active session for a candidate and campaign."""
        doc = await self.collection.find_one({
            "candidate_id": candidate_id,
            "campaign_id": campaign_id,
            "state": {"$nin": ["COMPLETED", "FAILED"]}
        })
        if not doc:
            return None
        return self._map_to_domain(doc)

    async def save(
        self, 
        session: InterviewSessionSchema, 
        expected_version: int,
        generation_fencing_id: Optional[str] = None,
        evaluation_fencing_id: Optional[str] = None,
        idempotency_question_id: Optional[str] = None,
        idempotency_evaluation_question_id: Optional[str] = None
    ) -> None:
        """
        Saves the mutated in-memory session.
        Uses OCC (expected_version) and dynamic conditional guards for embedded uniqueness.
        """
        SessionPersistenceValidator.validate(session)
        
        doc = self._map_to_bson(session)
        doc["version"] = expected_version + 1
        
        query: Dict[str, Any] = {
            "session_id": session.session_id,
            "version": expected_version
        }
        
        # Explicit fencing token protection
        if generation_fencing_id:
            query["generation_claim.claim_id"] = generation_fencing_id
            
        if evaluation_fencing_id:
            query["question_history.evaluation_claim.claim_id"] = evaluation_fencing_id
        
        # Defense in depth: embedded array duplicate guards
        if idempotency_evaluation_question_id:
            query["evaluation_history.question_record_id"] = {"$ne": idempotency_evaluation_question_id}
            
        if idempotency_question_id:
            query["question_history.record_id"] = {"$ne": idempotency_question_id}

        result = await self.collection.update_one(
            query,
            {"$set": doc},
            upsert=False
        )
        
        if result.matched_count == 0:
            exists = await self.collection.count_documents({"session_id": session.session_id})
            if exists == 0:
                if expected_version == 0:
                    await self.collection.insert_one(doc)
                    session.version = 1
                    return
                raise SessionNotFoundError(f"Session {session.session_id} not found.")
                
            # If it exists, let's determine why it failed.
            
            # 1. Idempotency Conflict (Highest Precedence)
            if idempotency_evaluation_question_id:
                idem_exists = await self.collection.count_documents({
                    "session_id": session.session_id,
                    "evaluation_history.question_record_id": idempotency_evaluation_question_id
                })
                if idem_exists > 0:
                    raise IdempotencyConflictError("Database rejected update due to embedded idempotency guard.")
                    
            if idempotency_question_id:
                idem_exists = await self.collection.count_documents({
                    "session_id": session.session_id,
                    "question_history.record_id": idempotency_question_id
                })
                if idem_exists > 0:
                    raise IdempotencyConflictError("Database rejected update due to embedded idempotency guard.")
                    
            # 2. Fencing Token Error (Second Precedence)
            if generation_fencing_id or evaluation_fencing_id:
                # To check if we lost the lease, we check if the token is absent.
                # If we were rejected and the token is absent from the current DB document, we lost the lease.
                fencing_query = {"session_id": session.session_id}
                if generation_fencing_id:
                    fencing_query["generation_claim.claim_id"] = generation_fencing_id
                if evaluation_fencing_id:
                    fencing_query["question_history.evaluation_claim.claim_id"] = evaluation_fencing_id
                    
                fencing_exists = await self.collection.count_documents(fencing_query)
                if fencing_exists == 0:
                    raise FencingTokenError("Operation finalized by stale worker who lost the lease.")
                    
            # 3. Generic OCC fallback (Lowest Precedence)
            raise OptimisticConcurrencyError(f"Stale write: expected version {expected_version}")
            
        session.version = expected_version + 1

    async def claim_evaluation(
        self, 
        session_id: str, 
        question_record_id: str, 
        expected_version: int,
        lease_seconds: int = 60
    ) -> OperationClaim:
        """
        Atomic claim for LLM evaluation.
        """
        now = datetime.now(timezone.utc)
        claim = OperationClaim(
            claim_id=str(uuid.uuid4()),
            claimed_at=now,
            expires_at=now + timedelta(seconds=lease_seconds)
        )
        claim_dict = claim.model_dump(mode="json")
        
        # We can claim IF:
        # 1) status is dispatched or answer_received (no claim exists)
        # OR 2) status is evaluating BUT the claim has expired
        query: Dict[str, Any] = {
            "session_id": session_id,
            "version": expected_version,
            "question_history.record_id": question_record_id,
            "$or": [
                {"question_history.status": {"$in": ["dispatched", "answer_received"]}},
                {
                    "question_history.status": "evaluating",
                    "question_history.evaluation_claim.expires_at": {"$lt": now.isoformat()}
                }
            ]
        }
        
        result = await self.collection.update_one(
            query,
            {
                "$set": {
                    "question_history.$[q].status": "evaluating",
                    "question_history.$[q].evaluation_claim": claim_dict
                },
                "$inc": {"version": 1}
            },
            array_filters=[{"q.record_id": question_record_id}]
        )
        
        if result.modified_count == 0:
            # Check if it was already held by someone else
            held = await self.collection.count_documents({
                "session_id": session_id,
                "version": expected_version,
                "question_history.record_id": question_record_id,
                "question_history.status": "evaluating",
                "question_history.evaluation_claim.expires_at": {"$gte": now.isoformat()}
            })
            if held > 0:
                raise ClaimAlreadyHeldError("Evaluation lease is actively held by another worker.")
            raise OptimisticConcurrencyError("Failed to claim evaluation: OCC failure or not found.")
            
        return claim

    async def claim_question_generation(
        self, 
        session_id: str, 
        expected_version: int,
        lease_seconds: int = 60
    ) -> OperationClaim:
        """
        Atomic claim for LLM Question Generation.
        """
        now = datetime.now(timezone.utc)
        claim = OperationClaim(
            claim_id=str(uuid.uuid4()),
            claimed_at=now,
            expires_at=now + timedelta(seconds=lease_seconds)
        )
        claim_dict = claim.model_dump(mode="json")
        
        query: Dict[str, Any] = {
            "session_id": session_id,
            "version": expected_version,
            "$or": [
                {"generation_claim": None},
                {"generation_claim.expires_at": {"$lt": now.isoformat()}}
            ]
        }
        
        result = await self.collection.update_one(
            query,
            {
                "$set": {"generation_claim": claim_dict},
                "$inc": {"version": 1}
            }
        )
        
        if result.modified_count == 0:
            held = await self.collection.count_documents({
                "session_id": session_id,
                "version": expected_version,
                "generation_claim.expires_at": {"$gte": now.isoformat()}
            })
            if held > 0:
                raise ClaimAlreadyHeldError("Generation lease is actively held by another worker.")
            raise OptimisticConcurrencyError("Failed to claim generation: OCC failure.")
            
        return claim

    async def release_question_generation(self, session_id: str, current_version: int, claim_id: str) -> None:
        """
        Explicitly release a generation claim (e.g. on fatal error).
        Requires the correct claim_id (fencing).
        """
        await self.collection.update_one(
            {
                "session_id": session_id,
                "version": current_version,
                "generation_claim.claim_id": claim_id
            },
            {
                "$set": {"generation_claim": None},
                "$inc": {"version": 1}
            }
        )

    async def release_evaluation(self, session_id: str, question_record_id: str, current_version: int, claim_id: str) -> None:
        """
        Explicitly release an evaluation claim and revert status.
        Requires the correct claim_id (fencing).
        """
        await self.collection.update_one(
            {
                "session_id": session_id,
                "version": current_version,
                "question_history.record_id": question_record_id,
                "question_history.evaluation_claim.claim_id": claim_id
            },
            {
                "$set": {
                    "question_history.$[q].evaluation_claim": None,
                    "question_history.$[q].status": "answer_received"
                },
                "$inc": {"version": 1}
            },
            array_filters=[{"q.record_id": question_record_id}]
        )
