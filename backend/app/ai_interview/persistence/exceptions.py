class PersistenceError(Exception):
    """Base exception for all persistence errors."""
    pass

class OptimisticConcurrencyError(PersistenceError):
    """Raised when the expected version of a document does not match the database version."""
    pass

class IdempotencyConflictError(PersistenceError):
    """Raised when an operation is rejected by the database due to an idempotency guard (e.g. duplicate evaluation)."""
    pass

class SessionNotFoundError(PersistenceError):
    """Raised when an interview session is not found."""
    pass

class FencingTokenError(PersistenceError):
    """Raised when an operation is finalized by a stale worker who no longer owns the active lease."""
    pass

class ClaimAlreadyHeldError(PersistenceError):
    """Raised when attempting to acquire a lease that is currently held and not expired."""
    pass

class PersistenceInvariantError(PersistenceError):
    """Raised when a Session fails structural persistence validation before saving."""
    pass
