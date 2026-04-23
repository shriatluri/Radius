"""Typed exception hierarchy for Radius API errors."""


class RadiusError(Exception):
    """Base exception for all Radius API errors."""

    def __init__(self, code: str, message: str, status_code: int, response=None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(f"[{status_code}] {code}: {message}")


class BadRequestError(RadiusError):
    """400 — invalid request parameters."""


class AuthenticationError(RadiusError):
    """401 — missing or invalid API key."""


class ForbiddenError(RadiusError):
    """403 — valid key but insufficient scopes."""


class NotFoundError(RadiusError):
    """404 — resource does not exist."""


class RateLimitError(RadiusError):
    """429 — too many requests."""

    def __init__(self, code, message, status_code, response=None, retry_after=None):
        super().__init__(code, message, status_code, response)
        self.retry_after = retry_after


class ServerError(RadiusError):
    """5xx — something went wrong on the server."""


_STATUS_MAP = {
    400: BadRequestError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
    429: RateLimitError,
}


def raise_for_status(response):
    """Raise a typed RadiusError if the HTTP response is not 2xx."""
    if response.ok:
        return

    # Try to extract structured error body
    code, message = "api_error", response.text
    try:
        body = response.json()
        err = body.get("error", {})
        code = err.get("code", code)
        message = err.get("message", message)
    except Exception:
        pass

    status = response.status_code
    exc_cls = _STATUS_MAP.get(status, ServerError if status >= 500 else RadiusError)

    if exc_cls is RateLimitError:
        retry_after = response.headers.get("Retry-After")
        raise RateLimitError(code, message, status, response, retry_after=retry_after)

    raise exc_cls(code, message, status, response)
