"""
Risk scoring engine for transactions.

Evaluates transactions based on:
- Sanctions checks (OFAC SDN via OFACScreener)
- Amount thresholds
- Chain risk
- Wallet patterns
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .sanctions import check_sanctions, is_high_risk_wallet

logger = logging.getLogger(__name__)


@dataclass
class RiskResult:
    """Result of risk scoring."""

    score: int
    level: str
    sanctions_result: str          # "passed" | "failed"
    required_actions: list[str]

    # Rich sanctions data — populated when sanctions_result == "failed"
    sdn_name: str = ""             # OFAC entity name e.g. "Lazarus Group"
    sdn_id: str = ""               # OFAC profile ID e.g. "27307"
    sdn_program: str = ""          # OFAC program e.g. "DPRK3", "CYBER2"
    list_source: str = ""          # "OFAC_SDN" | "OFAC_SDN_FALLBACK"
    sanctions_reason: str = ""     # Human-readable summary for logs/display


def score_transaction(
    amount: str,
    chain: str,
    from_wallet: Optional[str] = None,
    to_wallet: Optional[str] = None,
) -> RiskResult:
    """
    Score a transaction for risk.

    Checks (in order):
    1. Sanctions — both wallets screened against OFAC SDN live data
    2. High-risk wallet patterns (mixers, blenders)
    3. Amount thresholds
    4. Chain risk

    Sanctions hits return immediately with score=100 / level=critical.
    All other factors combine additively.
    """
    amt = Decimal(amount)
    score = 10
    required_actions: list[str] = []

    # ----------------------------------------------------------------
    # 1. Sanctions screening — exit early on any hit
    # ----------------------------------------------------------------
    for wallet in [from_wallet, to_wallet]:
        match = check_sanctions(wallet)
        if match.matched:
            reason = _build_reason(match)
            logger.warning(
                "sanctions_check",
                extra={
                    "event": "sanctions_check",
                    "wallet": wallet,
                    "result": "failed",
                    "sdn_name": match.name,
                    "sdn_id": match.sdn_id,
                    "sdn_program": match.program,
                    "list_source": match.list_source,
                },
            )
            logger.warning(
                "transaction_blocked",
                extra={
                    "event": "transaction_blocked",
                    "reason": "sanctioned_wallet",
                    "wallet": wallet,
                    "sdn_name": match.name,
                    "sdn_program": match.program,
                },
            )
            return RiskResult(
                score=100,
                level="critical",
                sanctions_result="failed",
                required_actions=["blocked_sanctioned_wallet"],
                sdn_name=match.name,
                sdn_id=match.sdn_id,
                sdn_program=match.program,
                list_source=match.list_source,
                sanctions_reason=reason,
            )
        logger.info(
            "sanctions_check",
            extra={
                "event": "sanctions_check",
                "wallet": wallet,
                "result": "passed",
            },
        )

    # ----------------------------------------------------------------
    # 2. High-risk wallet patterns (flagged, not blocked)
    # ----------------------------------------------------------------
    for wallet in [from_wallet, to_wallet]:
        if is_high_risk_wallet(wallet):
            score += 30
            required_actions.append("high_risk_wallet_review")

    # ----------------------------------------------------------------
    # 3. Amount-based risk
    # ----------------------------------------------------------------
    if amt >= Decimal("10000"):
        score += 40
    elif amt >= Decimal("1000"):
        score += 20

    # ----------------------------------------------------------------
    # 4. Chain risk
    # ----------------------------------------------------------------
    if chain.lower() not in {"ethereum", "polygon", "solana", "base"}:
        score += 10

    # ----------------------------------------------------------------
    # Determine level
    # ----------------------------------------------------------------
    if score >= 80:
        level = "critical"
        if "manual_review" not in required_actions:
            required_actions.append("manual_review")
    elif score >= 60:
        level = "high"
        if "manual_review" not in required_actions:
            required_actions.append("manual_review")
    elif score >= 30:
        level = "medium"
    else:
        level = "low"

    final_score = min(score, 100)
    logger.info(
        "risk_scored",
        extra={
            "event": "risk_scored",
            "score": final_score,
            "level": level,
            "factors": required_actions,
            "amount": str(amt),
            "chain": chain,
        },
    )
    return RiskResult(
        score=final_score,
        level=level,
        sanctions_result="passed",
        required_actions=required_actions,
    )


def _build_reason(match) -> str:
    """Build a human-readable sanctions reason string from a SanctionsMatch."""
    parts = [match.list_source or "OFAC_SDN"]
    if match.program:
        parts.append(match.program)
    if match.name:
        parts.append(match.name)
    return " — ".join(parts)
