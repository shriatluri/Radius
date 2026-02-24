"""
Rate limiting middleware using the Token Bucket algorithm.

How it works:
- Each API key gets a "bucket" with tokens
- Each request consumes 1 token
- Tokens refill at a steady rate (e.g., 100/minute)
- When bucket is empty, requests are rejected with 429

This approach:
- Allows bursts (use all tokens at once)
- Smooths out traffic over time
- Is simple to understand and implement
- Matches what Stripe/GitHub/etc use

Configuration:
- RATE_LIMIT_TOKENS: Max tokens in bucket (burst capacity)
- RATE_LIMIT_REFILL_RATE: Tokens added per second
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .config import settings

# Export configuration values for backward compatibility
RATE_LIMIT_TOKENS = settings.rate_limit_tokens
RATE_LIMIT_REFILL_RATE = settings.rate_limit_refill_rate


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    limit: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds until tokens available


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using token bucket.

    Good for single-server deployments. For multi-server,
    use Redis-backed implementation instead.
    """

    def __init__(
        self,
        max_tokens: int = RATE_LIMIT_TOKENS,
        refill_rate: float = RATE_LIMIT_REFILL_RATE,
    ):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.buckets: dict[str, dict] = {}  # key -> {tokens, last_refill}

    def _get_bucket(self, key: str) -> dict:
        """Get or create a bucket for a key."""
        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.max_tokens,
                "last_refill": time.time(),
            }
        return self.buckets[key]

    def _refill(self, bucket: dict) -> None:
        """Add tokens based on time elapsed since last refill."""
        now = time.time()
        elapsed = now - bucket["last_refill"]
        tokens_to_add = elapsed * self.refill_rate

        bucket["tokens"] = min(
            self.max_tokens,
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_refill"] = now

    def check(self, key: str, cost: int = 1) -> RateLimitResult:
        """
        Check if request is allowed and consume tokens.

        Args:
            key: Unique identifier (usually API key ID or IP)
            cost: Number of tokens to consume (default 1)

        Returns:
            RateLimitResult with allowed status and metadata
        """
        bucket = self._get_bucket(key)
        self._refill(bucket)

        # Calculate reset time (when bucket would be full again)
        tokens_needed = self.max_tokens - bucket["tokens"]
        seconds_to_full = tokens_needed / self.refill_rate if self.refill_rate > 0 else 0
        reset_at = datetime.utcnow() + timedelta(seconds=seconds_to_full)

        if bucket["tokens"] >= cost:
            bucket["tokens"] -= cost
            return RateLimitResult(
                allowed=True,
                remaining=int(bucket["tokens"]),
                limit=self.max_tokens,
                reset_at=reset_at,
            )
        else:
            # Calculate retry-after
            tokens_needed = cost - bucket["tokens"]
            retry_after = int(tokens_needed / self.refill_rate) + 1

            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=self.max_tokens,
                reset_at=reset_at,
                retry_after=retry_after,
            )

    def reset(self, key: str) -> None:
        """Reset a bucket (for testing or admin override)."""
        if key in self.buckets:
            del self.buckets[key]


class DatabaseRateLimiter:
    """
    Database-backed rate limiter for multi-server deployments.

    Uses the rate_limit_buckets table for persistence.
    Note: For high-traffic production, Redis is recommended.
    """

    def __init__(
        self,
        db: Session,
        max_tokens: int = RATE_LIMIT_TOKENS,
        refill_rate: float = RATE_LIMIT_REFILL_RATE,
    ):
        self.db = db
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate

    def check(self, key: str, endpoint: str = "default", cost: int = 1) -> RateLimitResult:
        """Check rate limit using database storage."""
        from app.db import models as db_models

        now = datetime.utcnow()

        # Find or create bucket
        bucket = self.db.query(db_models.RateLimitBucket).filter(
            db_models.RateLimitBucket.api_key_id == key,
            db_models.RateLimitBucket.endpoint == endpoint,
        ).first()

        if not bucket:
            # Create new bucket
            bucket = db_models.RateLimitBucket(
                api_key_id=key,
                endpoint=endpoint,
                tokens=self.max_tokens,
                last_refill=now,
            )
            self.db.add(bucket)
            self.db.commit()
            self.db.refresh(bucket)

        # Refill tokens based on elapsed time
        elapsed = (now - bucket.last_refill).total_seconds()
        tokens_to_add = elapsed * self.refill_rate
        bucket.tokens = min(self.max_tokens, bucket.tokens + int(tokens_to_add))
        bucket.last_refill = now

        # Calculate reset time
        tokens_needed = self.max_tokens - bucket.tokens
        seconds_to_full = tokens_needed / self.refill_rate if self.refill_rate > 0 else 0
        reset_at = now + timedelta(seconds=seconds_to_full)

        if bucket.tokens >= cost:
            bucket.tokens -= cost
            self.db.commit()

            return RateLimitResult(
                allowed=True,
                remaining=bucket.tokens,
                limit=self.max_tokens,
                reset_at=reset_at,
            )
        else:
            self.db.commit()

            tokens_needed = cost - bucket.tokens
            retry_after = int(tokens_needed / self.refill_rate) + 1

            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=self.max_tokens,
                reset_at=reset_at,
                retry_after=retry_after,
            )


# Global in-memory rate limiter instance
_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def check_rate_limit(
    key: str,
    cost: int = 1,
) -> RateLimitResult:
    """
    Check rate limit for a key.

    This is the main function to call from endpoints.
    """
    return _rate_limiter.check(key, cost)


def rate_limit_headers(result: RateLimitResult) -> dict[str, str]:
    """
    Generate standard rate limit headers.

    These headers follow the IETF draft standard:
    https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers
    """
    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(int(result.reset_at.timestamp())),
    }

    if result.retry_after is not None:
        headers["Retry-After"] = str(result.retry_after)

    return headers


def raise_rate_limit_exceeded(result: RateLimitResult) -> None:
    """Raise HTTPException for rate limit exceeded."""
    raise HTTPException(
        status_code=429,
        detail={
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests. Please slow down.",
                "retry_after": result.retry_after,
            }
        },
        headers=rate_limit_headers(result),
    )
