"""
Unit tests for the Travel Rule engine.

Covers:
  - detect_jurisdiction()     — ISO code → Jurisdiction mapping, EU member states
  - is_self_hosted_wallet()   — entity type → self-hosted flag
  - check_travel_rule()       — per-jurisdiction thresholds, cross-border stricter
                                rule, self-hosted verification, unknown fallback

All tests are pure unit tests — no database, no network, no API client.
"""

import pytest
from decimal import Decimal

from app.services.travel_rule import (
    EU_MEMBER_STATES,
    Jurisdiction,
    TravelRuleResult,
    check_travel_rule,
    detect_jurisdiction,
    is_self_hosted_wallet,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BUSINESS_WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
USER_WALLET = "0x742d35Cc6634C0532925a3b8D4C9C79D3b3B4123"


def _check(
    amount: str | int | Decimal,
    orig_jurisdiction: str = "US",
    benef_jurisdiction: str = "US",
    orig_entity: str = "business",
    benef_entity: str = "business",
    orig_wallet: str | None = BUSINESS_WALLET,
    benef_wallet: str | None = BUSINESS_WALLET,
) -> TravelRuleResult:
    """Shorthand wrapper for check_travel_rule with sensible defaults."""
    return check_travel_rule(
        amount_usd=Decimal(str(amount)),
        originator_jurisdiction=orig_jurisdiction,
        beneficiary_jurisdiction=benef_jurisdiction,
        originator_entity_type=orig_entity,
        beneficiary_entity_type=benef_entity,
        originator_wallet=orig_wallet,
        beneficiary_wallet=benef_wallet,
    )


# ---------------------------------------------------------------------------
# detect_jurisdiction()
# ---------------------------------------------------------------------------


class TestDetectJurisdiction:

    def test_known_jurisdictions_map_directly(self):
        assert detect_jurisdiction("US") == Jurisdiction.US
        assert detect_jurisdiction("UK") == Jurisdiction.UK
        assert detect_jurisdiction("SG") == Jurisdiction.SG
        assert detect_jurisdiction("JP") == Jurisdiction.JP
        assert detect_jurisdiction("AU") == Jurisdiction.AU

    def test_eu_label_maps_to_eu(self):
        assert detect_jurisdiction("EU") == Jurisdiction.EU

    @pytest.mark.parametrize("code", ["DE", "FR", "IT", "ES", "NL", "PL", "BE", "AT"])
    def test_eu_member_states_map_to_eu(self, code):
        """All EU member state codes must route to Jurisdiction.EU."""
        assert detect_jurisdiction(code) == Jurisdiction.EU

    def test_all_eu_member_states_covered(self):
        """Every entry in EU_MEMBER_STATES must resolve to Jurisdiction.EU."""
        for code in EU_MEMBER_STATES:
            result = detect_jurisdiction(code)
            assert result == Jurisdiction.EU, f"{code!r} should map to EU"

    def test_none_returns_unknown(self):
        assert detect_jurisdiction(None) == Jurisdiction.UNKNOWN

    def test_empty_string_returns_unknown(self):
        assert detect_jurisdiction("") == Jurisdiction.UNKNOWN

    def test_unrecognised_code_returns_unknown(self):
        assert detect_jurisdiction("ZZ") == Jurisdiction.UNKNOWN
        assert detect_jurisdiction("XX") == Jurisdiction.UNKNOWN

    def test_input_is_case_insensitive(self):
        assert detect_jurisdiction("us") == Jurisdiction.US
        assert detect_jurisdiction("uk") == Jurisdiction.UK
        assert detect_jurisdiction("sg") == Jurisdiction.SG


# ---------------------------------------------------------------------------
# is_self_hosted_wallet()
# ---------------------------------------------------------------------------


class TestIsSelfHostedWallet:

    def test_user_wallet_is_self_hosted(self):
        assert is_self_hosted_wallet(USER_WALLET, "user") is True

    def test_vasp_wallet_is_not_self_hosted(self):
        assert is_self_hosted_wallet(BUSINESS_WALLET, "vasp") is False

    def test_business_wallet_is_not_self_hosted(self):
        assert is_self_hosted_wallet(BUSINESS_WALLET, "business") is False

    def test_none_wallet_is_not_self_hosted(self):
        assert is_self_hosted_wallet(None, "user") is False

    def test_unknown_entity_type_is_treated_as_self_hosted(self):
        """Unknown entities are conservatively flagged as self-hosted."""
        assert is_self_hosted_wallet(USER_WALLET, "unknown") is True


# ---------------------------------------------------------------------------
# check_travel_rule() — US jurisdiction
# ---------------------------------------------------------------------------


class TestTravelRuleUS:
    """US BSA threshold: $3,000."""

    def test_below_threshold_not_required(self):
        result = _check(amount="2999", orig_jurisdiction="US", benef_jurisdiction="US")

        assert result.status == "not_required"
        assert result.threshold_exceeded is False
        assert result.jurisdiction == "US"

    def test_at_threshold_required(self):
        result = _check(amount="3000", orig_jurisdiction="US", benef_jurisdiction="US")

        assert result.status == "required"
        assert result.threshold_exceeded is True

    def test_above_threshold_required(self):
        result = _check(amount="5000", orig_jurisdiction="US", benef_jurisdiction="US")

        assert result.status == "required"
        assert result.threshold_exceeded is True

    def test_required_actions_populated(self):
        result = _check(amount="3000", orig_jurisdiction="US", benef_jurisdiction="US")

        assert "collect_originator_info" in result.required_actions
        assert "collect_beneficiary_info" in result.required_actions
        assert "transmit_travel_rule_data" in result.required_actions

    def test_not_required_has_no_transmit_action(self):
        result = _check(amount="500", orig_jurisdiction="US", benef_jurisdiction="US")

        assert "transmit_travel_rule_data" not in result.required_actions

    def test_threshold_and_currency_reported(self):
        result = _check(amount="500", orig_jurisdiction="US", benef_jurisdiction="US")

        assert result.applicable_threshold == Decimal("3000")
        assert result.threshold_currency == "USD"


# ---------------------------------------------------------------------------
# check_travel_rule() — EU jurisdiction (zero threshold)
# ---------------------------------------------------------------------------


class TestTravelRuleEU:
    """EU TFR: zero threshold (all CASP-to-CASP transfers), €1 000 self-hosted verification."""

    def test_any_positive_amount_required(self):
        """EU zero threshold means even $0.01 triggers Travel Rule."""
        result = _check(amount="0.01", orig_jurisdiction="EU", benef_jurisdiction="EU")

        assert result.status == "required"
        assert result.threshold_exceeded is True

    def test_zero_threshold_currency_eur(self):
        result = _check(amount="100", orig_jurisdiction="EU", benef_jurisdiction="EU")

        assert result.applicable_threshold == Decimal("0")
        assert result.threshold_currency == "EUR"

    def test_self_hosted_below_verification_threshold_is_required_not_verification(self):
        """
        EU + user wallet + amount < €1000 equiv (~$1080):
        threshold exceeded (EU zero) but self-hosted verification NOT triggered.
        Status = "required", not "verification_required".
        """
        result = _check(
            amount="500",           # below €1000 self-hosted verification threshold
            orig_jurisdiction="EU",
            benef_jurisdiction="EU",
            orig_entity="user",
            orig_wallet=USER_WALLET,
        )

        assert result.status == "required"
        assert result.threshold_exceeded is True
        assert result.self_hosted_verification_needed is False

    def test_self_hosted_above_verification_threshold_is_verification_required(self):
        """
        EU + user wallet + amount >= €1000 equiv ($1080):
        self-hosted verification required → status = "verification_required".
        """
        result = _check(
            amount="1100",          # above €1000 self-hosted threshold (~$1080)
            orig_jurisdiction="EU",
            benef_jurisdiction="EU",
            orig_entity="user",
            orig_wallet=USER_WALLET,
        )

        assert result.status == "verification_required"
        assert result.self_hosted_verification_needed is True
        assert "verify_self_hosted_wallet_ownership" in result.required_actions

    def test_business_entity_no_self_hosted_verification(self):
        """Business wallets are not self-hosted — no ownership verification needed."""
        result = _check(
            amount="5000",
            orig_jurisdiction="EU",
            benef_jurisdiction="EU",
            orig_entity="business",
            orig_wallet=BUSINESS_WALLET,
        )

        assert result.status == "required"
        assert result.self_hosted_verification_needed is False

    def test_eu_member_state_code_applies_eu_rules(self):
        """'IT', 'ES', etc. must route to EU jurisdiction and apply its zero threshold."""
        for code in ("IT", "ES", "NL", "PL"):
            result = _check(amount="0.01", orig_jurisdiction=code, benef_jurisdiction=code)
            assert result.status == "required", f"Expected required for {code} with €0.01"
            assert result.jurisdiction == "EU", f"Expected EU jurisdiction for {code}"


# ---------------------------------------------------------------------------
# check_travel_rule() — UK jurisdiction
# ---------------------------------------------------------------------------


class TestTravelRuleUK:
    """UK FCA threshold: £1,000 ≈ $1,250 USD equivalent."""

    def test_below_threshold_not_required(self):
        # £999 ≈ $1249 — just under $1250 USD equivalent
        result = _check(amount="1249", orig_jurisdiction="UK", benef_jurisdiction="UK")

        assert result.status == "not_required"
        assert result.threshold_exceeded is False

    def test_at_threshold_required(self):
        # £1,000 = $1,250 USD equivalent (exact threshold)
        result = _check(amount="1250", orig_jurisdiction="UK", benef_jurisdiction="UK")

        assert result.status in ("required", "verification_required")
        assert result.threshold_exceeded is True

    def test_threshold_currency_is_gbp(self):
        result = _check(amount="500", orig_jurisdiction="UK", benef_jurisdiction="UK")

        assert result.threshold_currency == "GBP"
        assert result.applicable_threshold == Decimal("1000")


# ---------------------------------------------------------------------------
# check_travel_rule() — Singapore
# ---------------------------------------------------------------------------


class TestTravelRuleSingapore:
    """Singapore MAS threshold: SGD 1,500 ≈ $1,100 USD equivalent."""

    def test_below_threshold_not_required(self):
        # SGD 1,499 ≈ $1,099
        result = _check(amount="1099", orig_jurisdiction="SG", benef_jurisdiction="SG")

        assert result.status == "not_required"
        assert result.threshold_exceeded is False

    def test_at_threshold_required(self):
        # SGD 1,500 ≈ $1,100 (exact USD equivalent in the rules table)
        result = _check(amount="1100", orig_jurisdiction="SG", benef_jurisdiction="SG")

        assert result.threshold_exceeded is True

    def test_threshold_currency_is_sgd(self):
        result = _check(amount="500", orig_jurisdiction="SG", benef_jurisdiction="SG")

        assert result.threshold_currency == "SGD"
        assert result.applicable_threshold == Decimal("1500")


# ---------------------------------------------------------------------------
# check_travel_rule() — Unknown jurisdiction (FATF default)
# ---------------------------------------------------------------------------


class TestTravelRuleUnknown:
    """Unknown jurisdiction falls back to FATF $1,000 default."""

    def test_below_fatf_default_not_required(self):
        result = _check(amount="999", orig_jurisdiction="ZZ", benef_jurisdiction="ZZ")

        assert result.status == "not_required"

    def test_at_fatf_default_required(self):
        result = _check(amount="1000", orig_jurisdiction="ZZ", benef_jurisdiction="ZZ")

        assert result.status == "required"
        assert result.threshold_exceeded is True

    def test_unknown_code_applies_fatf_rules(self):
        result = _check(amount="500", orig_jurisdiction="UNKNOWN_CODE", benef_jurisdiction="US")

        # FATF $1000 vs US $3000 — FATF is stricter
        assert result.applicable_threshold == Decimal("1000")
        assert result.jurisdiction == "UNKNOWN"


# ---------------------------------------------------------------------------
# check_travel_rule() — cross-border (stricter threshold applies)
# ---------------------------------------------------------------------------


class TestTravelRuleCrossBorder:
    """When jurisdictions differ, the lower USD-equivalent threshold governs."""

    def test_us_to_eu_uses_eu_zero_threshold(self):
        """
        US ($3,000) → EU ($0): EU is stricter, so even $500 must comply.
        """
        result = _check(amount="500", orig_jurisdiction="US", benef_jurisdiction="EU")

        assert result.status == "required"
        assert result.threshold_exceeded is True
        assert result.jurisdiction == "EU"

    def test_eu_to_us_also_uses_eu_zero_threshold(self):
        result = _check(amount="500", orig_jurisdiction="EU", benef_jurisdiction="US")

        assert result.threshold_exceeded is True
        assert result.jurisdiction == "EU"

    def test_us_to_us_uses_us_3000_threshold(self):
        """Sanity check: same-jurisdiction uses its own threshold."""
        below = _check(amount="2999", orig_jurisdiction="US", benef_jurisdiction="US")
        at = _check(amount="3000", orig_jurisdiction="US", benef_jurisdiction="US")

        assert below.status == "not_required"
        assert at.status == "required"

    def test_uk_to_sg_uses_sg_as_stricter(self):
        """
        UK ($1,250 equiv) → SG ($1,100 equiv): SG is stricter.
        $1,150 is above SG ($1,100) but logic picks the lower threshold.
        """
        result = _check(amount="1150", orig_jurisdiction="UK", benef_jurisdiction="SG")

        assert result.threshold_exceeded is True
        assert result.jurisdiction == "SG"

    def test_sg_to_uk_uses_sg_as_stricter(self):
        result = _check(amount="1150", orig_jurisdiction="SG", benef_jurisdiction="UK")

        assert result.threshold_exceeded is True
        assert result.jurisdiction == "SG"

    def test_us_to_unknown_uses_fatf_threshold(self):
        """
        US ($3,000) vs UNKNOWN ($1,000 FATF): FATF is stricter.
        $1,500 triggers under FATF but not under US rules.
        """
        result = _check(amount="1500", orig_jurisdiction="US", benef_jurisdiction="ZZ")

        assert result.threshold_exceeded is True
        assert result.jurisdiction == "UNKNOWN"


# ---------------------------------------------------------------------------
# check_travel_rule() — self-hosted wallet verification
# ---------------------------------------------------------------------------


class TestSelfHostedWalletVerification:
    """Self-hosted wallet rules differ by jurisdiction."""

    def test_us_user_wallet_no_verification_required(self):
        """US does not require self-hosted wallet ownership verification."""
        result = _check(
            amount="5000",
            orig_jurisdiction="US",
            benef_jurisdiction="US",
            orig_entity="user",
            orig_wallet=USER_WALLET,
        )

        assert result.self_hosted_verification_needed is False
        assert result.status == "required"   # still required (above $3k threshold)

    def test_eu_user_wallet_high_amount_triggers_verification(self):
        result = _check(
            amount="2000",          # well above €1000 self-hosted threshold
            orig_jurisdiction="EU",
            benef_jurisdiction="EU",
            orig_entity="user",
            orig_wallet=USER_WALLET,
        )

        assert result.self_hosted_verification_needed is True
        assert result.status == "verification_required"

    def test_eu_vasp_wallet_no_verification(self):
        """VASP-hosted wallets are not self-hosted — no extra verification."""
        result = _check(
            amount="2000",
            orig_jurisdiction="EU",
            benef_jurisdiction="EU",
            orig_entity="vasp",
            orig_wallet=BUSINESS_WALLET,
        )

        assert result.self_hosted_verification_needed is False

    def test_no_wallet_no_self_hosted_flag(self):
        """None wallet → is_self_hosted returns False → no verification action."""
        result = _check(
            amount="2000",
            orig_jurisdiction="EU",
            benef_jurisdiction="EU",
            orig_entity="user",
            orig_wallet=None,
        )

        assert result.self_hosted_verification_needed is False
