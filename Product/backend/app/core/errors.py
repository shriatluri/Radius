"""
Custom exceptions for the Radius API.

Provides structured error responses across all endpoints.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class RadiusError(Exception):
    """Base exception for Radius API errors."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


async def radius_error_handler(request: Request, exc: RadiusError) -> JSONResponse:
    """Exception handler for RadiusError."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
