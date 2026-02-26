"""
Travel Rule threshold logic with jurisdiction support.

Implements FATF Recommendation 16 thresholds for 30+ jurisdictions.
Handles self-hosted wallet verification requirements.

References:
- FATF Recommendation 16 (June 2025 update)
- EU Transfer of Funds Regulation (TFR) 2023/1113
- FinCEN BSA Travel Rule
- MAS Payment Services Act
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class Jurisdiction(str, Enum):
    """Supported jurisdictions for Travel Rule compliance."""

    # Americas
    US = "US"
    CA = "CA"  # Canada

    # Europe
    EU = "EU"  # European Union (covers all 27 member states)
    UK = "UK"
    CH = "CH"  # Switzerland
    DE = "DE"  # Germany (uses EU rules)
    FR = "FR"  # France (uses EU rules)
    LI = "LI"  # Liechtenstein

    # Asia Pacific
    SG = "SG"  # Singapore
    JP = "JP"  # Japan
    HK = "HK"  # Hong Kong
    KR = "KR"  # South Korea
    AU = "AU"  # Australia
    MY = "MY"  # Malaysia
    PH = "PH"  # Philippines
    IN = "IN"  # India
    ID = "ID"  # Indonesia

    # Middle East
    AE = "AE"  # UAE (Abu Dhabi/Dubai)
    BH = "BH"  # Bahrain

    # Other
    BS = "BS"  # Bahamas
    BM = "BM"  # Bermuda
    GI = "GI"  # Gibraltar
    IM = "IM"  # Isle of Man
    JE = "JE"  # Jersey
    ZA = "ZA"  # South Africa

    # Default/Unknown
    UNKNOWN = "UNKNOWN"


@dataclass
class JurisdictionRule:
    """Travel Rule requirements for a specific jurisdiction."""

    threshold_amount: Decimal  # In local currency, 0 = all transactions
    threshold_currency: str
    threshold_usd_equivalent: Decimal  # For comparison when currencies differ
    requires_self_hosted_verification: bool
    self_hosted_verification_threshold: Optional[Decimal]  # None = same as main threshold
    enforcement_date: str
    notes: str


# Jurisdiction rules database
# Thresholds as of February 2025
# USD equivalents are approximate for comparison purposes
JURISDICTION_RULES: dict[Jurisdiction, JurisdictionRule] = {
    # United States - $3,000 threshold (BSA Travel Rule)
    Jurisdiction.US: JurisdictionRule(
        threshold_amount=Decimal("3000"),
        threshold_currency="USD",
        threshold_usd_equivalent=Decimal("3000"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2013-03-13",
        notes="FinCEN BSA Travel Rule. Proposed $250 threshold for international transfers pending.",
    ),

    # European Union - €0 threshold (all transactions), €1000 for self-hosted verification
    Jurisdiction.EU: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="EUR",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1000"),  # €1,000
        enforcement_date="2024-12-30",
        notes="TFR 2023/1113. Zero threshold for CASP-to-CASP. Wallet ownership verification required for self-hosted >€1000.",
    ),

    # United Kingdom - £1,000 threshold
    Jurisdiction.UK: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="GBP",
        threshold_usd_equivalent=Decimal("1250"),  # Approximate
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1000"),
        enforcement_date="2023-09-01",
        notes="FCA guidance. Risk-based PII collection for self-hosted wallets.",
    ),

    # Switzerland - CHF 1,000 threshold
    Jurisdiction.CH: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="CHF",
        threshold_usd_equivalent=Decimal("1100"),  # Approximate
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1000"),
        enforcement_date="2020-01-01",
        notes="FINMA rules. Must verify wallet owner identity. 30-day linked transaction aggregation.",
    ),

    # Germany - €1,000 (follows EU but had earlier implementation)
    Jurisdiction.DE: JurisdictionRule(
        threshold_amount=Decimal("0"),  # Now aligned with EU TFR
        threshold_currency="EUR",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1000"),
        enforcement_date="2024-12-30",
        notes="Follows EU TFR. Previously €1000 threshold under national rules.",
    ),

    # France - €0 (EU rules)
    Jurisdiction.FR: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="EUR",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1000"),
        enforcement_date="2024-12-30",
        notes="Follows EU TFR.",
    ),

    # Liechtenstein - €0 threshold
    Jurisdiction.LI: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="EUR",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-04-01",
        notes="Enhanced due diligence required for self-hosted wallets.",
    ),

    # Singapore - SGD 1,500 threshold
    Jurisdiction.SG: JurisdictionRule(
        threshold_amount=Decimal("1500"),
        threshold_currency="SGD",
        threshold_usd_equivalent=Decimal("1100"),  # Approximate
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1500"),
        enforcement_date="2020-01-28",
        notes="MAS Payment Services Act. Identity verification required for self-hosted wallets.",
    ),

    # Japan - ¥0 threshold (all transactions)
    Jurisdiction.JP: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="JPY",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2023-06-01",
        notes="JVCEA rules. No minimum threshold.",
    ),

    # Hong Kong - HKD 8,000 threshold
    Jurisdiction.HK: JurisdictionRule(
        threshold_amount=Decimal("8000"),
        threshold_currency="HKD",
        threshold_usd_equivalent=Decimal("1025"),  # Approximate
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2023-06-01",
        notes="SFC/HKMA rules. Highest major jurisdiction threshold.",
    ),

    # South Korea - ₩1,000,000 threshold
    Jurisdiction.KR: JurisdictionRule(
        threshold_amount=Decimal("1000000"),
        threshold_currency="KRW",
        threshold_usd_equivalent=Decimal("750"),  # Approximate
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-03-25",
        notes="FSC rules. Very high nominal threshold.",
    ),

    # Canada - CAD 1,000 threshold
    Jurisdiction.CA: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="CAD",
        threshold_usd_equivalent=Decimal("740"),  # Approximate
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-03-31",
        notes="FINTRAC rules. Enhanced records at CAD 10,000+.",
    ),

    # Australia - A$0 threshold (grace period until Jul 2026)
    Jurisdiction.AU: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="AUD",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2026-07-01",
        notes="AUSTRAC rules. Grace period until July 2026.",
    ),

    # Malaysia - RM 0 threshold
    Jurisdiction.MY: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="MYR",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-04-01",
        notes="BNM rules. No minimum threshold.",
    ),

    # Philippines - PHP 50,000 threshold
    Jurisdiction.PH: JurisdictionRule(
        threshold_amount=Decimal("50000"),
        threshold_currency="PHP",
        threshold_usd_equivalent=Decimal("900"),  # Approximate
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("50000"),
        enforcement_date="2021-08-10",
        notes="BSP rules. Enhanced due diligence for self-hosted wallets.",
    ),

    # India - ₹0 threshold
    Jurisdiction.IN: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="INR",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2023-03-10",
        notes="FIU-IND rules. No minimum threshold.",
    ),

    # Indonesia - $1,000 threshold
    Jurisdiction.ID: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="USD",
        threshold_usd_equivalent=Decimal("1000"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-04-29",
        notes="BAPPEBTI rules.",
    ),

    # UAE (Abu Dhabi) - AED 0 threshold
    Jurisdiction.AE: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="AED",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2023-12-21",
        notes="ADGM/VARA rules. No minimum threshold.",
    ),

    # Bahrain - BHD 0 threshold
    Jurisdiction.BH: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="BHD",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2020-01-01",
        notes="CBB rules. Earliest adopter. No minimum threshold.",
    ),

    # Bahamas - $1,000 threshold
    Jurisdiction.BS: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="BSD",
        threshold_usd_equivalent=Decimal("1000"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-03-16",
        notes="SCB rules.",
    ),

    # Bermuda - $0 threshold
    Jurisdiction.BM: JurisdictionRule(
        threshold_amount=Decimal("0"),
        threshold_currency="BMD",
        threshold_usd_equivalent=Decimal("0"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2022-02-27",
        notes="BMA rules. No minimum threshold.",
    ),

    # Gibraltar - £1,000 threshold
    Jurisdiction.GI: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="GBP",
        threshold_usd_equivalent=Decimal("1250"),
        requires_self_hosted_verification=True,
        self_hosted_verification_threshold=Decimal("1000"),
        enforcement_date="2022-09-22",
        notes="GFSC rules. PII collection for self-hosted wallets.",
    ),

    # Isle of Man - £1,000 threshold
    Jurisdiction.IM: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="GBP",
        threshold_usd_equivalent=Decimal("1250"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2024-10-28",
        notes="FSA rules. Recently implemented.",
    ),

    # South Africa - ZAR 5,000 threshold
    Jurisdiction.ZA: JurisdictionRule(
        threshold_amount=Decimal("5000"),
        threshold_currency="ZAR",
        threshold_usd_equivalent=Decimal("275"),  # Approximate
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2025-04-30",
        notes="FSCA rules. Upcoming enforcement.",
    ),

    # Unknown jurisdiction - use FATF recommended threshold
    Jurisdiction.UNKNOWN: JurisdictionRule(
        threshold_amount=Decimal("1000"),
        threshold_currency="USD",
        threshold_usd_equivalent=Decimal("1000"),
        requires_self_hosted_verification=False,
        self_hosted_verification_threshold=None,
        enforcement_date="2019-06-21",
        notes="FATF Recommendation 16 default threshold.",
    ),
}


# EU member states - all follow EU TFR
EU_MEMBER_STATES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
}


@dataclass
class TravelRuleResult:
    """Result of Travel Rule threshold check."""

    status: str  # "required", "not_required", "verification_required"
    threshold_exceeded: bool
    applicable_threshold: Decimal
    threshold_currency: str
    jurisdiction: str
    required_actions: list[str]
    self_hosted_verification_needed: bool
    notes: str


def detect_jurisdiction(country_code: Optional[str]) -> Jurisdiction:
    """
    Detect jurisdiction from ISO 3166-1 alpha-2 country code.

    EU member states are mapped to EU jurisdiction.
    """
    if not country_code:
        return Jurisdiction.UNKNOWN

    code = country_code.upper()

    # Check if EU member state
    if code in EU_MEMBER_STATES:
        return Jurisdiction.EU

    # Try direct mapping
    try:
        return Jurisdiction(code)
    except ValueError:
        return Jurisdiction.UNKNOWN


def is_self_hosted_wallet(wallet: Optional[str], entity_type: str) -> bool:
    """
    Determine if a wallet is self-hosted (unhosted).

    Self-hosted wallets are those not controlled by a VASP/CASP.
    In practice, this is determined by:
    - Entity type being "user" without a VASP association
    - Wallet not being in a known VASP custody address list
    """
    if not wallet:
        return False

    # If entity is a VASP or business with custody, it's hosted
    if entity_type in ("vasp", "business"):
        return False

    # User wallets are typically self-hosted unless proven otherwise
    # In a real implementation, you'd check against known VASP custody addresses
    if entity_type == "user":
        return True

    # Unknown entities treated as potentially self-hosted for safety
    return True


def check_travel_rule(
    amount_usd: Decimal,
    originator_jurisdiction: Optional[str],
    beneficiary_jurisdiction: Optional[str],
    originator_entity_type: str,
    beneficiary_entity_type: str,
    originator_wallet: Optional[str] = None,
    beneficiary_wallet: Optional[str] = None,
) -> TravelRuleResult:
    """
    Check if a transaction requires Travel Rule compliance.

    Uses the STRICTER threshold when multiple jurisdictions are involved.

    Args:
        amount_usd: Transaction amount in USD (or USD-equivalent)
        originator_jurisdiction: ISO country code of originator
        beneficiary_jurisdiction: ISO country code of beneficiary
        originator_entity_type: Type of originator ("user", "business", "vasp")
        beneficiary_entity_type: Type of beneficiary ("user", "business", "vasp")
        originator_wallet: Originator wallet address
        beneficiary_wallet: Beneficiary wallet address

    Returns:
        TravelRuleResult with compliance status and required actions
    """
    # Detect jurisdictions
    orig_jurisdiction = detect_jurisdiction(originator_jurisdiction)
    benef_jurisdiction = detect_jurisdiction(beneficiary_jurisdiction)

    # Get rules for both jurisdictions
    orig_rule = JURISDICTION_RULES.get(orig_jurisdiction, JURISDICTION_RULES[Jurisdiction.UNKNOWN])
    benef_rule = JURISDICTION_RULES.get(benef_jurisdiction, JURISDICTION_RULES[Jurisdiction.UNKNOWN])

    # Use the STRICTER (lower) threshold
    if orig_rule.threshold_usd_equivalent <= benef_rule.threshold_usd_equivalent:
        applicable_rule = orig_rule
        applicable_jurisdiction = orig_jurisdiction
    else:
        applicable_rule = benef_rule
        applicable_jurisdiction = benef_jurisdiction

    required_actions: list[str] = []
    notes_parts: list[str] = []

    # Check if threshold is exceeded
    threshold_exceeded = amount_usd >= applicable_rule.threshold_usd_equivalent

    # Check for self-hosted wallet involvement
    orig_is_self_hosted = is_self_hosted_wallet(originator_wallet, originator_entity_type)
    benef_is_self_hosted = is_self_hosted_wallet(beneficiary_wallet, beneficiary_entity_type)
    involves_self_hosted = orig_is_self_hosted or benef_is_self_hosted

    # Determine self-hosted verification requirements
    self_hosted_verification_needed = False
    if involves_self_hosted and applicable_rule.requires_self_hosted_verification:
        verification_threshold = applicable_rule.self_hosted_verification_threshold or applicable_rule.threshold_amount
        # Convert verification threshold to USD for comparison
        # For simplicity, we use the same conversion factor
        if applicable_rule.threshold_currency == "EUR":
            verification_threshold_usd = verification_threshold * Decimal("1.08")  # Approximate EUR/USD
        elif applicable_rule.threshold_currency == "GBP":
            verification_threshold_usd = verification_threshold * Decimal("1.25")  # Approximate GBP/USD
        elif applicable_rule.threshold_currency == "CHF":
            verification_threshold_usd = verification_threshold * Decimal("1.10")  # Approximate CHF/USD
        else:
            verification_threshold_usd = verification_threshold

        if amount_usd >= verification_threshold_usd:
            self_hosted_verification_needed = True
            required_actions.append("verify_self_hosted_wallet_ownership")
            if orig_is_self_hosted:
                notes_parts.append("Originator wallet requires ownership verification")
            if benef_is_self_hosted:
                notes_parts.append("Beneficiary wallet requires ownership verification")

    # Determine final status
    if threshold_exceeded:
        required_actions.append("collect_originator_info")
        required_actions.append("collect_beneficiary_info")
        required_actions.append("transmit_travel_rule_data")

        if self_hosted_verification_needed:
            status = "verification_required"
            notes_parts.insert(0, f"Travel Rule required ({applicable_jurisdiction.value}) with self-hosted wallet verification")
        else:
            status = "required"
            notes_parts.insert(0, f"Travel Rule required ({applicable_jurisdiction.value})")
    else:
        status = "not_required"
        notes_parts.append(f"Below threshold of {applicable_rule.threshold_amount} {applicable_rule.threshold_currency}")

    # Add jurisdiction-specific notes
    if applicable_jurisdiction == Jurisdiction.EU:
        notes_parts.append("EU TFR requires compliance for ALL CASP-to-CASP transfers")
    elif applicable_jurisdiction == Jurisdiction.US:
        notes_parts.append("FinCEN may lower threshold to $250 for international transfers")
    elif applicable_jurisdiction == Jurisdiction.CH:
        notes_parts.append("Swiss rules aggregate linked transactions within 30 days")

    return TravelRuleResult(
        status=status,
        threshold_exceeded=threshold_exceeded,
        applicable_threshold=applicable_rule.threshold_amount,
        threshold_currency=applicable_rule.threshold_currency,
        jurisdiction=applicable_jurisdiction.value,
        required_actions=required_actions,
        self_hosted_verification_needed=self_hosted_verification_needed,
        notes=" | ".join(notes_parts),
    )


def get_required_data_fields(jurisdiction: str) -> dict:
    """
    Get the required IVMS101 data fields for a jurisdiction.

    Returns a dict describing required originator and beneficiary fields.
    """
    # Base FATF required fields (IVMS101 standard)
    base_fields = {
        "originator": {
            "required": [
                "full_name",
                "account_number_or_wallet",
            ],
            "required_one_of": [
                "address",
                "date_of_birth",
                "national_id",
            ],
        },
        "beneficiary": {
            "required": [
                "full_name",
                "account_number_or_wallet",
            ],
            "optional": [
                "country",
                "town",
            ],
        },
        "transaction": {
            "required": [
                "amount",
                "asset_type",
                "unique_reference",
            ],
        },
    }

    # EU requires additional fields
    if jurisdiction in ("EU", "DE", "FR") or jurisdiction in EU_MEMBER_STATES:
        base_fields["originator"]["required"].extend([
            "address",
            "date_of_birth",
        ])
        base_fields["beneficiary"]["required"].extend([
            "country",
            "town",
        ])

    # US requires execution date and institution info
    if jurisdiction == "US":
        base_fields["transaction"]["required"].extend([
            "execution_date",
            "originator_institution",
            "beneficiary_institution",
        ])

    return base_fields
