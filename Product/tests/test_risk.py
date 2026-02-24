"""
Unit tests for the risk scoring engine.

Covers score_transaction() in app.services.risk:
  - Sanctions screening (early exit, SDN field population)
  - Amount thresholds (>=$1 000, >=$10 000, boundary values)
  - Chain risk (known vs unknown chains)
  - High-risk wallet patterns (+30 per wallet)
  - Combined factors and score cap
  - Level thresholds (low / medium / high / critical)

check_sanctions() and is_high_risk_wallet() are always patched so these
tests exercise risk.py in pure isolation — no OFAC data or network calls.
"""

import pytest
from contextlib import contextmanager
from unittest.mock import patch

from app.services.ofac import SanctionsMatch
from app.services.risk import RiskResult, score_transaction

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLEAN_WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
SANCTIONED_WALLET = "0x8589427373d6d84e98730d7795d8f6f8731fda16"

NO_MATCH = SanctionsMatch(matched=False)

SANCTIONS_HIT = SanctionsMatch(
    matched=True,
    name="TORNADO CASH",
    sdn_id="36072",
    currency="ETH",
    program="CYBER2",
    list_source="OFAC_SDN",
)


# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------


@contextmanager
def _patch_clean():
    """Both wallets pass sanctions; neither is high-risk."""
    with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
         patch("app.services.risk.is_high_risk_wallet", return_value=False):
        yield


def _sanctions_side_effect(wallet):
    """Return a hit for SANCTIONED_WALLET, clean for everything else."""
    if wallet and wallet.lower() == SANCTIONED_WALLET:
        return SANCTIONS_HIT
    return NO_MATCH


# ---------------------------------------------------------------------------
# Sanctions screening
# ---------------------------------------------------------------------------


class TestSanctionsScreening:
    """score_transaction() exits immediately on any sanctions hit."""

    def test_sanctioned_from_wallet_is_blocked(self):
        with patch("app.services.risk.check_sanctions", side_effect=_sanctions_side_effect), \
             patch("app.services.risk.is_high_risk_wallet", return_value=False):
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet=SANCTIONED_WALLET,
                to_wallet=CLEAN_WALLET,
            )

        assert result.score == 100
        assert result.level == "critical"
        assert result.sanctions_result == "failed"
        assert result.required_actions == ["blocked_sanctioned_wallet"]

    def test_sanctioned_to_wallet_is_blocked(self):
        with patch("app.services.risk.check_sanctions", side_effect=_sanctions_side_effect), \
             patch("app.services.risk.is_high_risk_wallet", return_value=False):
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet=CLEAN_WALLET,
                to_wallet=SANCTIONED_WALLET,
            )

        assert result.score == 100
        assert result.level == "critical"
        assert result.sanctions_result == "failed"

    def test_sanctioned_wallet_populates_sdn_fields(self):
        with patch("app.services.risk.check_sanctions", side_effect=_sanctions_side_effect), \
             patch("app.services.risk.is_high_risk_wallet", return_value=False):
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet=SANCTIONED_WALLET,
                to_wallet=CLEAN_WALLET,
            )

        assert result.sdn_name == "TORNADO CASH"
        assert result.sdn_id == "36072"
        assert result.sdn_program == "CYBER2"
        assert result.list_source == "OFAC_SDN"
        # _build_reason joins list_source, program, name with " — "
        assert "OFAC_SDN" in result.sanctions_reason
        assert "CYBER2" in result.sanctions_reason
        assert "TORNADO CASH" in result.sanctions_reason

    def test_clean_wallets_pass_sanctions(self):
        with _patch_clean():
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet=CLEAN_WALLET,
                to_wallet=CLEAN_WALLET,
            )

        assert result.sanctions_result == "passed"
        assert result.score < 100


# ---------------------------------------------------------------------------
# Amount thresholds
# ---------------------------------------------------------------------------


class TestAmountRisk:
    """Amount-based scoring: +20 for >= $1 000, +40 for >= $10 000."""

    def test_low_amount_no_addition(self):
        """$500 → base 10, level low."""
        with _patch_clean():
            result = score_transaction(amount="500", chain="ethereum")

        assert result.score == 10
        assert result.level == "low"

    def test_mid_amount_adds_20(self):
        """$1 000 exactly → +20 → score 30, level medium."""
        with _patch_clean():
            result = score_transaction(amount="1000", chain="ethereum")

        assert result.score == 30
        assert result.level == "medium"

    def test_high_amount_adds_40(self):
        """$10 000 exactly → +40 → score 50, level medium."""
        with _patch_clean():
            result = score_transaction(amount="10000", chain="ethereum")

        assert result.score == 50
        assert result.level == "medium"

    def test_very_high_amount_adds_40(self):
        """$50 000 → +40 (same bucket as $10 000)."""
        with _patch_clean():
            result = score_transaction(amount="50000", chain="ethereum")

        assert result.score == 50

    # -- boundary values --

    def test_boundary_just_below_1000(self):
        """$999.99 → no amount addition → score 10."""
        with _patch_clean():
            result = score_transaction(amount="999.99", chain="ethereum")

        assert result.score == 10

    def test_boundary_exactly_1000(self):
        """$1 000.00 → +20 → score 30."""
        with _patch_clean():
            result = score_transaction(amount="1000.00", chain="ethereum")

        assert result.score == 30

    def test_boundary_just_below_10000(self):
        """$9 999.99 → +20 (mid bucket)."""
        with _patch_clean():
            result = score_transaction(amount="9999.99", chain="ethereum")

        assert result.score == 30

    def test_boundary_exactly_10000(self):
        """$10 000.00 → +40 (high bucket)."""
        with _patch_clean():
            result = score_transaction(amount="10000.00", chain="ethereum")

        assert result.score == 50


# ---------------------------------------------------------------------------
# Chain risk
# ---------------------------------------------------------------------------


class TestChainRisk:
    """Unknown chains add +10 to the score."""

    @pytest.mark.parametrize("chain", ["ethereum", "polygon", "solana", "base"])
    def test_known_chains_no_addition(self, chain):
        with _patch_clean():
            result = score_transaction(amount="500", chain=chain)

        assert result.score == 10

    @pytest.mark.parametrize("chain", ["binance", "tron", "avalanche", "unknown_chain"])
    def test_unknown_chains_add_10(self, chain):
        with _patch_clean():
            result = score_transaction(amount="500", chain=chain)

        assert result.score == 20

    def test_chain_comparison_is_case_insensitive(self):
        """'Ethereum' and 'ETHEREUM' should not trigger the unknown-chain penalty."""
        with _patch_clean():
            upper = score_transaction(amount="500", chain="ETHEREUM")
            mixed = score_transaction(amount="500", chain="Ethereum")

        assert upper.score == 10
        assert mixed.score == 10


# ---------------------------------------------------------------------------
# High-risk wallet patterns
# ---------------------------------------------------------------------------


class TestHighRiskWalletPattern:
    """Mixer/tornado/blender patterns add +30 per matched wallet."""

    def test_high_risk_from_wallet_adds_30(self):
        def _is_high_risk(wallet):
            return wallet == "mixer_wallet"

        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", side_effect=_is_high_risk):
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet="mixer_wallet",
                to_wallet=CLEAN_WALLET,
            )

        assert result.score == 40   # 10 base + 30
        assert result.level == "medium"
        assert "high_risk_wallet_review" in result.required_actions

    def test_high_risk_to_wallet_adds_30(self):
        def _is_high_risk(wallet):
            return wallet == "tornado_wallet"

        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", side_effect=_is_high_risk):
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet=CLEAN_WALLET,
                to_wallet="tornado_wallet",
            )

        assert result.score == 40
        assert "high_risk_wallet_review" in result.required_actions

    def test_both_wallets_high_risk_adds_60(self):
        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", return_value=True):
            result = score_transaction(
                amount="500",
                chain="ethereum",
                from_wallet="mixer_a",
                to_wallet="mixer_b",
            )

        assert result.score == 70   # 10 + 30 + 30
        assert result.level == "high"


# ---------------------------------------------------------------------------
# Combined factors + score cap
# ---------------------------------------------------------------------------


class TestCombinedFactors:
    """Multiple risk factors combine additively, capped at 100."""

    def test_combined_amount_chain_risk(self):
        """$5 000 on an unknown chain: 10 + 20 + 10 = 40, medium."""
        with _patch_clean():
            result = score_transaction(amount="5000", chain="tron")

        assert result.score == 40
        assert result.level == "medium"

    def test_combined_high_risk_wallet_and_amount(self):
        """One high-risk wallet + $10 000: 10 + 30 + 40 = 80, critical."""
        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", side_effect=lambda w: w == "mixer_wallet"):
            result = score_transaction(
                amount="10000",
                chain="ethereum",
                from_wallet="mixer_wallet",
                to_wallet=CLEAN_WALLET,
            )

        assert result.score == 80
        assert result.level == "critical"
        assert "manual_review" in result.required_actions

    def test_score_capped_at_100(self):
        """Both wallets high-risk + $10 000 + unknown chain: raw 120, capped 100."""
        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", return_value=True):
            result = score_transaction(
                amount="10000",
                chain="tron",
                from_wallet="mixer_a",
                to_wallet="mixer_b",
            )

        # 10 + 30 + 30 + 40 + 10 = 120, capped to 100
        assert result.score == 100

    def test_manual_review_added_for_high_level(self):
        """Score in [60, 79] triggers level=high and adds manual_review action."""
        # One high-risk wallet: 10 + 30 + 20 + 10 = 70 → high
        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", side_effect=lambda w: w == "mixer_wallet"):
            result = score_transaction(
                amount="5000",   # +20
                chain="tron",    # +10
                from_wallet="mixer_wallet",   # +30
                to_wallet=CLEAN_WALLET,       # +0
            )

        assert result.score == 70
        assert result.level == "high"
        assert "manual_review" in result.required_actions

    def test_no_wallets_scores_on_amount_and_chain_only(self):
        """None wallets are safely handled — only amount and chain matter."""
        with _patch_clean():
            result = score_transaction(amount="500", chain="ethereum")

        assert result.score == 10
        assert result.sanctions_result == "passed"


# ---------------------------------------------------------------------------
# Level threshold boundaries
# ---------------------------------------------------------------------------


class TestLevelThresholds:
    """Exact boundary verification for each risk level."""

    def test_score_29_is_low(self):
        # 10 base + unknown chain (10) + $999 amount (0) = 20 → low
        with _patch_clean():
            result = score_transaction(amount="999", chain="tron")
        assert result.score == 20
        assert result.level == "low"

    def test_score_30_is_medium(self):
        # 10 base + $1 000 (+20) = 30 → medium
        with _patch_clean():
            result = score_transaction(amount="1000", chain="ethereum")
        assert result.score == 30
        assert result.level == "medium"

    def test_score_60_is_high(self):
        # 10 + 30 (high-risk wallet) + 10 (unknown chain) + 10 (base already 10) = ...
        # Let's calculate: need score == 60
        # 10 base + 30 (one high-risk wallet) + 20 (amount $1000) = 60 → high
        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", side_effect=lambda w: w == "mixer"):
            result = score_transaction(
                amount="1000",
                chain="ethereum",
                from_wallet="mixer",
                to_wallet=CLEAN_WALLET,
            )
        assert result.score == 60
        assert result.level == "high"

    def test_score_80_is_critical(self):
        # 10 + 30 + 40 = 80 → critical
        with patch("app.services.risk.check_sanctions", return_value=NO_MATCH), \
             patch("app.services.risk.is_high_risk_wallet", side_effect=lambda w: w == "mixer"):
            result = score_transaction(
                amount="10000",
                chain="ethereum",
                from_wallet="mixer",
                to_wallet=CLEAN_WALLET,
            )
        assert result.score == 80
        assert result.level == "critical"
