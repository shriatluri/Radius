"""
Sanctions screening for Radius.

Primary source: OFAC SDN advanced XML via OFACScreener (real, auto-updating).
Fallback source: KNOWN_SANCTIONED_WALLETS (hardcoded set, used when OFAC data
  is unavailable and as test fixtures).

Call check_sanctions(wallet) — it always returns the richest result available.
"""

from __future__ import annotations

import logging
from typing import Optional

from .ofac import SanctionsMatch, get_screener

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback / test fixture list
# These are real OFAC-sanctioned addresses kept here so tests and offline
# development work without downloading the full SDN XML.
# Do NOT use this set as the primary screening source in production.
# ---------------------------------------------------------------------------

KNOWN_SANCTIONED_WALLETS: set[str] = {
    # Tornado Cash (OFAC sanctioned Aug 2022 — CYBER2 program)
    "0x8589427373d6d84e98730d7795d8f6f8731fda16",  # Router
    "0x722122df12d4e14e13ac3b6895a86e84145b6967",  # Proxy
    "0xdd4c48c0b24039969fc16d1cdf626eab821d3384",  # 0.1 ETH
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",  # 1 ETH
    "0xd96f2b1c14db8458374d9aca76e26c3d18364307",  # 10 ETH
    "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d",  # 100 ETH
    # Lazarus Group / APT38 (DPRK — DPRK3 program)
    "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
    "0xa0e1c89ef1a489c9c7de96311ed5ce5d32c20e4b",
    # Garantex (Russian exchange — UKRAINE-EO13685 program)
    "0x6f1ca141a28907f78ebaa64fb83a9088b02a8352",
}

# High-risk wallet patterns — flagged but not blocked
HIGH_RISK_PATTERNS: frozenset[str] = frozenset({"mixer", "tornado", "blender"})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_sanctions(wallet: Optional[str]) -> SanctionsMatch:
    """
    Check a wallet address against sanctions lists.

    Returns:
        SanctionsMatch with matched, name, sdn_id, currency, program, list_source.

    Screening order (controlled by SANCTIONS_PROVIDER env var):
      "opensanctions" (recommended for production):
        1. OpenSanctions API — covers OFAC + EU + UN + 40 other lists in one call
        2. Falls back to OFAC local if API is unavailable or times out
        3. Falls back to hardcoded list if OFAC local has no data
      "ofac_local" (default):
        1. OFAC SDN screener (live data, auto-refreshed daily)
        2. Hardcoded fallback list (if OFAC screener has no data)
      "none":
        Always returns no match — useful for test/sandbox environments.
    """
    if not wallet:
        return SanctionsMatch(matched=False)

    normalized = wallet.lower().strip()

    try:
        from app.core.config import settings
        provider = settings.sanctions_provider
    except Exception:
        provider = "ofac_local"

    if provider == "none":
        return SanctionsMatch(matched=False)

    # ── OpenSanctions (multi-list: OFAC + EU + UN + 40 others) ─────────────
    if provider == "opensanctions":
        try:
            from app.core.config import settings as _s
            from .opensanctions import check_wallet, OpenSanctionsError
            result = check_wallet(normalized, _s.opensanctions_api_key)
            if result.matched:
                return result
            # OpenSanctions returned a clean result — trust it, skip OFAC local
            return SanctionsMatch(matched=False)
        except Exception as exc:
            logger.warning(
                "opensanctions_unavailable",
                extra={
                    "event": "opensanctions_unavailable",
                    "error": str(exc),
                    "fallback": "ofac_local",
                },
            )
            # Fall through to OFAC local below

    elif provider not in ("ofac_local",):
        logger.warning(
            f"Unknown SANCTIONS_PROVIDER={provider!r}, falling back to ofac_local"
        )

    # ── OFAC local (US-only, live SDN XML) ──────────────────────────────────
    try:
        screener = get_screener()
        result = screener.check(normalized)
        if result.matched:
            logger.info(
                f"OFAC SDN match: wallet={normalized} name={result.name!r} "
                f"program={result.program!r} sdn_id={result.sdn_id!r}"
            )
            return result

        if screener.address_count > 0:
            return SanctionsMatch(matched=False)

    except Exception as exc:
        logger.warning(f"OFAC screener error, falling back to hardcoded list: {exc}")

    # ── Hardcoded fallback (offline / all screeners unavailable) ────────────
    if normalized in KNOWN_SANCTIONED_WALLETS:
        logger.warning(
            f"Matched via fallback hardcoded list: {normalized}. "
            "OFAC screener may not be loaded."
        )
        return SanctionsMatch(
            matched=True,
            name="",
            sdn_id="",
            list_source="OFAC_SDN_FALLBACK",
        )

    return SanctionsMatch(matched=False)


def is_high_risk_wallet(wallet: Optional[str]) -> bool:
    """
    Check if a wallet address matches known high-risk patterns.

    These are not blocked but trigger a manual review flag in the risk score.
    """
    if not wallet:
        return False
    normalized = wallet.lower()
    return any(pat in normalized for pat in HIGH_RISK_PATTERNS)


def get_sanctions_status() -> dict:
    """
    Return current status of the sanctions screener.
    Exposed via the /v1/health endpoint.
    """
    try:
        screener = get_screener()
        return screener.status()
    except Exception as exc:
        return {"loaded": False, "error": str(exc)}


