"""
Domain Exceptions.

These are application-level exceptions that the service layer raises.
They carry business meaning, not HTTP meaning.

Global exception handlers in main.py convert these to HTTP responses:
    NotFoundError       → 404
    AlreadyExistsError  → 409
    AuthenticationError → 401
    AuthorizationError  → 403

WHY NOT HTTPException IN SERVICES?
    Services might be called from a CLI tool, a background worker, or a
    test — none of which understand HTTP status codes. Domain exceptions
    separate business semantics from transport concerns.
"""


class AppException(Exception):
    """Base for all application exceptions."""

    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested entity does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, code="NOT_FOUND")


class AlreadyExistsError(AppException):
    """Raised when creating an entity that already exists (uniqueness violation)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, code="ALREADY_EXISTS")


class AuthenticationError(AppException):
    """
    Raised when identity cannot be verified.

    Covers: bad credentials, invalid token, expired token, inactive account.
    The service should NOT differentiate between these in user-facing messages
    for login (to prevent user enumeration), but CAN differentiate for
    already-authenticated requests (e.g., expired token vs inactive account).
    """

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(AppException):
    """
    Raised when the user is authenticated but lacks permission.

    Covers: wrong role, doesn't own the resource.
    """

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class InvalidStateError(AppException):
    """
    Raised when an operation is invalid for the current entity state.
    e.g., submitting an answer to a completed interview.
    Maps to 409 Conflict.
    """

    def __init__(self, message: str = "Invalid state for this operation"):
        super().__init__(message=message, code="INVALID_STATE")


class AIServiceError(AppException):
    """
    Raised when the AI service fails (upstream failure) and cannot be recovered via fallbacks.
    Maps to 502 Bad Gateway.
    """

    def __init__(self, message: str = "AI service is currently unavailable"):
        super().__init__(message=message, code="AI_SERVICE_ERROR")
