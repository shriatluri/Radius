"""
Unit tests for sanctions screening.

Covers:
  - OFACScreener.check() — direct screener lookup with a pre-seeded index
  - check_sanctions()    — full pipeline: OFAC screener → hardcoded fallback
  - is_high_risk_wallet() — pattern detection

No network calls, no file I/O. The OFACScreener is always seeded with
_loaded=True so it never attempts a download or cache read.
"""

import pytest
from unittest.mock import patch

from app.services.ofac import OFACScreener, SanctionsMatch
from app.services.sanctions import (
    KNOWN_SANCTIONED_WALLETS,
    check_sanctions,
    is_high_risk_wallet,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Real Tornado Cash router — present in KNOWN_SANCTIONED_WALLETS (CYBER2)
SANCTIONED_WALLET = "0x8589427373d6d84e98730d7795d8f6f8731fda16"

# A clean Ethereum address not on any sanctions list
CLEAN_WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

# What the index entry looks like after parsing the SDN XML
OFAC_INDEX_ENTRY = {
    "name": "TORNADO CASH",
    "sdn_id": "36072",
    "currency": "ETH",
    "program": "CYBER2",
    "address": SANCTIONED_WALLET,
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def make_screener(addresses: dict | None = None) -> OFACScreener:
    """
    Return a pre-loaded OFACScreener with a custom in-memory index.

    _loaded=True prevents any download/cache-read attempt, so tests stay
    fully offline and deterministic.
    """
    screener = OFACScreener()
    screener._loaded = True
    screener._index = addresses if addresses is not None else {}
    return screener


# ---------------------------------------------------------------------------
# OFACScreener.check() — direct unit tests
# ---------------------------------------------------------------------------


class TestOFACScreenerCheck:
    """Direct tests for OFACScreener.check() with a pre-seeded index."""

    def test_known_sanctioned_address_is_matched(self):
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        result = screener.check(SANCTIONED_WALLET)

        assert result.matched is True
        assert result.name == "TORNADO CASH"
        assert result.sdn_id == "36072"
        assert result.currency == "ETH"
        assert result.program == "CYBER2"
        assert result.list_source == "OFAC_SDN"

    def test_clean_address_not_matched(self):
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        result = screener.check(CLEAN_WALLET)

        assert result.matched is False

    def test_empty_wallet_not_matched(self):
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        result = screener.check("")

        assert result.matched is False

    def test_uppercase_address_matches(self):
        """Lookup is case-insensitive — uppercase input must hit the index."""
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        result = screener.check(SANCTIONED_WALLET.upper())

        assert result.matched is True

    def test_mixed_case_address_matches(self):
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        result = screener.check("0x8589427373D6D84E98730D7795D8f6f8731FDA16")

        assert result.matched is True

    def test_empty_index_returns_no_match(self):
        screener = make_screener({})
        result = screener.check(SANCTIONED_WALLET)

        assert result.matched is False


# ---------------------------------------------------------------------------
# check_sanctions() — OFAC screener + hardcoded fallback
# ---------------------------------------------------------------------------


class TestCheckSanctions:
    """
    Tests for check_sanctions(), which chains:
      OFAC SDN screener → KNOWN_SANCTIONED_WALLETS fallback

    get_screener() is patched in every test that would reach it, so no
    real OFAC data or network access is needed.
    """

    # -- early-exit paths (no screener access) --

    def test_none_wallet_returns_no_match(self):
        result = check_sanctions(None)
        assert result.matched is False

    def test_empty_string_returns_no_match(self):
        result = check_sanctions("")
        assert result.matched is False

    # -- SANCTIONS_PROVIDER=none --

    def test_provider_none_bypasses_all_screening(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "sanctions_provider", "none")
        result = check_sanctions(SANCTIONED_WALLET)

        assert result.matched is False

    # -- screener has data: trust it --

    def test_sanctioned_wallet_matched_via_screener(self):
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        with patch("app.services.sanctions.get_screener", return_value=screener):
            result = check_sanctions(SANCTIONED_WALLET)

        assert result.matched is True
        assert result.list_source == "OFAC_SDN"
        assert result.name == "TORNADO CASH"
        assert result.program == "CYBER2"

    def test_clean_wallet_not_matched_when_screener_has_data(self):
        """Screener has data (address_count > 0) but no hit → trusted clean."""
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        with patch("app.services.sanctions.get_screener", return_value=screener):
            result = check_sanctions(CLEAN_WALLET)

        assert result.matched is False

    def test_case_insensitive_input_to_check_sanctions(self):
        """Mixed-case input is normalised before screener lookup."""
        screener = make_screener({SANCTIONED_WALLET: OFAC_INDEX_ENTRY})
        with patch("app.services.sanctions.get_screener", return_value=screener):
            result = check_sanctions(SANCTIONED_WALLET.upper())

        assert result.matched is True

    # -- screener has no data: fall through to hardcoded list --

    def test_fallback_to_hardcoded_list_when_screener_empty(self):
        """
        When address_count == 0, check_sanctions falls through to
        KNOWN_SANCTIONED_WALLETS and returns list_source=OFAC_SDN_FALLBACK.
        """
        screener = make_screener({})  # address_count == 0
        with patch("app.services.sanctions.get_screener", return_value=screener):
            result = check_sanctions(SANCTIONED_WALLET)

        assert result.matched is True
        assert result.list_source == "OFAC_SDN_FALLBACK"

    def test_clean_wallet_not_matched_with_empty_screener(self):
        """Empty screener + address not in fallback list → not matched."""
        screener = make_screener({})
        with patch("app.services.sanctions.get_screener", return_value=screener):
            result = check_sanctions(CLEAN_WALLET)

        assert result.matched is False

    def test_all_fallback_wallets_are_caught(self):
        """Every address in KNOWN_SANCTIONED_WALLETS is caught by the fallback."""
        screener = make_screener({})
        with patch("app.services.sanctions.get_screener", return_value=screener):
            for wallet in KNOWN_SANCTIONED_WALLETS:
                result = check_sanctions(wallet)
                assert result.matched is True, f"Expected match for {wallet}"
                assert result.list_source == "OFAC_SDN_FALLBACK"

    # -- screener error: fall back to hardcoded list --

    def test_screener_exception_triggers_fallback(self):
        """If get_screener() raises, fall back to KNOWN_SANCTIONED_WALLETS."""
        with patch(
            "app.services.sanctions.get_screener",
            side_effect=RuntimeError("screener unavailable"),
        ):
            result = check_sanctions(SANCTIONED_WALLET)

        assert result.matched is True
        assert result.list_source == "OFAC_SDN_FALLBACK"

    def test_screener_exception_clean_wallet_returns_no_match(self):
        """Screener error + clean wallet → not in fallback list → not matched."""
        with patch(
            "app.services.sanctions.get_screener",
            side_effect=RuntimeError("screener unavailable"),
        ):
            result = check_sanctions(CLEAN_WALLET)

        assert result.matched is False


# ---------------------------------------------------------------------------
# is_high_risk_wallet() — pattern detection
# ---------------------------------------------------------------------------


class TestHighRiskWallet:
    """Tests for is_high_risk_wallet() — pattern matching, not sanctions."""

    def test_none_is_not_high_risk(self):
        assert is_high_risk_wallet(None) is False

    def test_empty_string_is_not_high_risk(self):
        assert is_high_risk_wallet("") is False

    def test_clean_wallet_is_not_high_risk(self):
        assert is_high_risk_wallet(CLEAN_WALLET) is False

    def test_mixer_pattern_detected(self):
        assert is_high_risk_wallet("mixer_service_wallet") is True

    def test_tornado_pattern_detected(self):
        assert is_high_risk_wallet("tornado_router_contract") is True

    def test_blender_pattern_detected(self):
        assert is_high_risk_wallet("blender_io_wallet") is True

    def test_patterns_are_case_insensitive(self):
        assert is_high_risk_wallet("TORNADO_CASH") is True
        assert is_high_risk_wallet("MIXER_SERVICE") is True
        assert is_high_risk_wallet("BLENDER_IO") is True

    def test_pattern_embedded_in_address(self):
        """Pattern anywhere in the string triggers the flag."""
        assert is_high_risk_wallet("0xtornado123abc") is True
