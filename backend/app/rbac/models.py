from enum import Enum


class UserRole(str, Enum):
    """
    User roles supported by IntelliHire.
    """

    ADMIN = "admin"
    COMPANY = "company"
    CANDIDATE = "candidate"