"""
OpenSanctions API client for multi-source sanctions screening.

OpenSanctions aggregates 40+ sanctions lists including:
  - OFAC SDN (US)
  - EU Consolidated Financial Sanctions (European Commission)
  - UN Security Council Consolidated List
  - UK HMT Financial Sanctions List
  - And 36+ others

Why this matters:
  OFAC alone only covers US-designated entities. EU VASPs are legally required
  to screen against the EU consolidated list; UK VASPs against UK HMT.
  Without these, a "passed" result from Radius is incomplete for non-US deals
  and can expose a customer to regulatory liability.

  OpenSanctions gives us all lists in a single API call instead of maintaining
  three separate XML parsers.

Docs: https://www.opensanctions.org/docs/api/
Free tier: https://www.opensanctions.org/api/ (startups, non-commercial)
"""

import logging
from typing import Optional

import requests

from .ofac import SanctionsMatch

logger = logging.getLogger(__name__)

# ---- Constants ---------------------------------------------------------------

_API_BASE = "https://api.opensanctions.org"
_DATASET = "sanctions"   # Covers OFAC + EU + UN + 40 other lists in one shot
_TIMEOUT = 5.0           # Seconds — fast fail so we can fall back to OFAC local

# Minimum match score to treat as a confirmed hit (0–1 scale).
# Crypto wallet address lookups always return 1.0 (exact match or nothing).
# 0.95 avoids false positives from fuzzy name matching while catching all
# address hits. Raise this if you see false positives; lower it never.
_MIN_SCORE = 0.95

# Human-readable labels for OpenSanctions dataset IDs we care about.
# Full dataset catalogue: https://www.opensanctions.org/datasets/
_DATASET_LABELS: dict[str, str] = {
    "us_ofac_sdn":         "OFAC_SDN",
    "eu_fsf":              "EU_FSF",
    "un_sc_sanctions":     "UN_SC",
    "gb_hmt_sanctions":    "UK_HMT",
    "ch_seco_sanctions":   "CH_SECO",
    "au_dfat_sanctions":   "AU_DFAT",
    "ca_dfatd_sema_sanctions": "CA_DFATD",
    "jp_mof_sanctions":    "JP_MOF",
}


# ---- Exceptions --------------------------------------------------------------

class OpenSanctionsError(Exception):
    """
    Raised when the OpenSanctions API is unreachable, times out, or returns
    a non-2xx status. The caller (check_sanctions) catches this and falls back
    to the OFAC local screener.
    """


# ---- Public API --------------------------------------------------------------

def check_wallet(wallet: str, api_key: str) -> SanctionsMatch:
    """
    Screen a single crypto wallet address against OpenSanctions.

    Args:
        wallet:  Normalised (lowercase) wallet address.
        api_key: OpenSanctions API key from settings.

    Returns:
        SanctionsMatch — matched=True if any list flags the address.

    Raises:
        OpenSanctionsError — on timeout, HTTP error, or unexpected response.
        The caller should catch this and fall back to OFAC local.

    Why we use CryptoWallet schema:
        OpenSanctions stores wallet addresses as CryptoWallet entities linked
        to sanctioned persons/orgs. Querying with this schema gives us a
        direct address lookup rather than a fuzzy name search.
    """
    payload = {
        "queries": {
            "wallet": {
                "schema": "CryptoWallet",
                "properties": {
                    "publicKey": [wallet],
                },
            }
        }
    }

    try:
        resp = requests.post(
            f"{_API_BASE}/match/{_DATASET}",
            json=payload,
            headers={"Authorization": f"ApiKey {api_key}"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.Timeout as exc:
        raise OpenSanctionsError(f"Timeout after {_TIMEOUT}s: {exc}") from exc
    except requests.HTTPError as exc:
        raise OpenSanctionsError(
            f"HTTP {exc.response.status_code} from OpenSanctions API"
        ) from exc
    except requests.RequestException as exc:
        raise OpenSanctionsError(f"Request failed: {exc}") from exc

    try:
        data = resp.json()
    except Exception as exc:
        raise OpenSanctionsError(f"Invalid JSON response: {exc}") from exc

    results = data.get("responses", {}).get("wallet", {}).get("results", [])

    for result in results:
        score = result.get("score", 0.0)
        if score < _MIN_SCORE:
            continue

        datasets: list[str] = result.get("datasets", [])
        list_source = _format_list_source(datasets)

        props = result.get("properties", {})
        name_list = props.get("name", [])
        name = name_list[0] if name_list else ""

        programs = props.get("program", props.get("programs", []))
        program = programs[0] if programs else ""

        logger.info(
            "opensanctions_hit",
            extra={
                "event": "opensanctions_hit",
                "wallet": wallet,
                "name": name,
                "datasets": ",".join(datasets),
                "score": score,
                "list_source": list_source,
            },
        )

        return SanctionsMatch(
            matched=True,
            name=name,
            sdn_id=result.get("id", ""),
            program=program,
            list_source=list_source,
        )

    return SanctionsMatch(matched=False)


# ---- Helpers -----------------------------------------------------------------

def _format_list_source(datasets: list[str]) -> str:
    """
    Convert OpenSanctions dataset IDs into a readable list-source string.

    Examples:
        ["us_ofac_sdn"]                  → "OFAC_SDN"
        ["eu_fsf", "us_ofac_sdn"]        → "EU_FSF,OFAC_SDN"
        ["un_sc_sanctions"]              → "UN_SC"
        ["some_unknown_dataset"]         → "OPENSANCTIONS"
    """
    labels = []
    for ds in datasets:
        if ds in _DATASET_LABELS:
            labels.append(_DATASET_LABELS[ds])
        elif ds.startswith("opensanctions"):
            # Skip the aggregator meta-dataset itself
            pass
        else:
            # Unknown list — include the raw ID, truncated, so it's visible in logs
            labels.append(ds.upper()[:20])

    return ",".join(labels) if labels else "OPENSANCTIONS"
