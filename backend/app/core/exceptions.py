"""NetSage Core Custom Exceptions.

Defines unified application exceptions mapped to standard HTTP error codes
and consistent JSON response payloads across the NetSage REST API.
"""

from typing import Any, Optional


class NetSageException(Exception):
    """Base exception for all NetSage application errors."""

    def __init__(
        self,
        detail: Any,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
    ):
        super().__init__(str(detail))
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code


class NetSageNotFoundException(NetSageException):
    """Raised when a requested resource (e.g. session, question) does not exist."""

    def __init__(self, detail: str = "Resource not found.", error_code: str = "NOT_FOUND"):
        super().__init__(detail=detail, status_code=404, error_code=error_code)


class NetSageBadRequestException(NetSageException):
    """Raised when an invalid operation is attempted (e.g. answering completed session)."""

    def __init__(self, detail: str = "Bad request.", error_code: str = "BAD_REQUEST"):
        super().__init__(detail=detail, status_code=400, error_code=error_code)


class NetSageConflictException(NetSageException):
    """Raised when contradictory evidence or conflicting diagnostic state is detected."""

    def __init__(
        self,
        detail: Any = "Contradictory state detected in diagnostic session.",
        error_code: str = "CONFLICT_DETECTED",
    ):
        super().__init__(detail=detail, status_code=409, error_code=error_code)


class NetSageValidationException(NetSageException):
    """Raised when input validation fails."""

    def __init__(self, detail: Any = "Validation error.", error_code: str = "VALIDATION_ERROR"):
        super().__init__(detail=detail, status_code=422, error_code=error_code)

