"""
OFAC SDN digital currency address screener.

Downloads and parses the OFAC Specially Designated Nationals (SDN) Advanced XML,
extracting all digital currency (crypto) addresses for real-time sanctions screening.

Data source:
  https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml

Updated daily by the US Treasury. Covers all OFAC programs (CYBER, DPRK, IRAN, etc.).

Parsing strategy:
  The advanced XML has three sections that must be joined:
  1. ReferenceValueSets > FeatureTypeValues — maps FeatureType IDs to human-readable
     names like "Digital Currency Address - ETH"
  2. DistinctParties > DistinctParty > Profile > Feature — maps Profile IDs to
     their digital currency addresses using FeatureTypeID references
  3. SdnList > SdnEntry — maps Profile IDs to entity names, SDN IDs, and programs

  We join: SdnEntry.profileId → Profile.ID → Feature.FeatureTypeID → FeatureType.ID
"""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# OFAC SDN Advanced XML (Treasury.gov)
OFAC_SDN_XML_URL = "https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml"

# XML namespace (updated by OFAC in May 2024)
SDN_NS = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED_XML"

# Where to store downloaded + parsed data
_BACKEND_DIR = Path(__file__).parent.parent.parent
DATA_DIR = _BACKEND_DIR / "data" / "ofac"


@dataclass
class SanctionsMatch:
    """Result of an OFAC SDN address check."""

    matched: bool
    name: str = ""
    sdn_id: str = ""
    currency: str = ""
    program: str = ""
    list_source: str = "OFAC_SDN"


class OFACScreener:
    """
    OFAC SDN digital currency address screener.

    Downloads, caches, and queries the OFAC advanced XML list for sanctioned
    crypto wallet addresses. Provides O(1) lookup after initial parse.

    Usage:
        screener = OFACScreener()
        result = screener.check("0x8589427373d6d84e98730d7795d8f6f8731fda16")
        if result.matched:
            print(f"Sanctioned: {result.name} ({result.program})")
    """

    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        refresh_hours: int = 24,
        sdn_url: str = OFAC_SDN_XML_URL,
    ):
        self.data_dir = data_dir
        self.refresh_hours = refresh_hours
        self._sdn_url = sdn_url

        # In-memory address index: {lowercase_address: entry_dict}
        self._index: dict[str, dict] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _xml_file(self) -> Path:
        return self.data_dir / "sdn_advanced.xml"

    def _index_file(self) -> Path:
        return self.data_dir / "address_index.json"

    def _meta_file(self) -> Path:
        return self.data_dir / "meta.json"

    def _read_meta(self) -> dict:
        f = self._meta_file()
        if f.exists():
            try:
                return json.loads(f.read_text())
            except Exception:
                pass
        return {}

    def _write_meta(self, meta: dict) -> None:
        self._meta_file().write_text(json.dumps(meta, indent=2))

    def _is_stale(self) -> bool:
        last = self._read_meta().get("last_updated")
        if not last:
            return True
        return datetime.now(timezone.utc).replace(tzinfo=None) - datetime.fromisoformat(last) > timedelta(hours=self.refresh_hours)

    def _t(self, name: str) -> str:
        """Return a namespace-qualified XML tag name."""
        return f"{{{SDN_NS}}}{name}"

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self) -> bool:
        """
        Download the OFAC SDN advanced XML to disk.

        Streams the file (~80 MB) in 1 MB chunks. Returns True on success.
        Does not overwrite the existing file on failure.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.data_dir / "sdn_advanced.xml.tmp"

        logger.info(f"Downloading OFAC SDN advanced XML from {self._sdn_url} ...")
        try:
            resp = requests.get(self._sdn_url, timeout=180, stream=True)
            resp.raise_for_status()

            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

            # Atomic replace only on success
            tmp.replace(self._xml_file())
            size_mb = self._xml_file().stat().st_size / (1024 * 1024)
            logger.info(f"OFAC download complete: {size_mb:.1f} MB")
            return True

        except requests.RequestException as exc:
            logger.error(f"OFAC download failed: {exc}")
            if tmp.exists():
                tmp.unlink()
            return False

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse(self) -> dict[str, dict]:
        """
        Parse the cached OFAC advanced XML and extract all digital currency addresses.

        Three-pass parse over the actual XML schema:

          Pass 1 — ReferenceValueSets/FeatureTypeValues:
            Build {feature_type_id → currency_symbol} for "Digital Currency Address - *" types.

          Pass 2 — DistinctParties:
            For each Profile, extract:
              - crypto addresses from Feature[@FeatureTypeID in crypto_types]/FeatureVersion/VersionDetail
              - primary name from Identity/Alias[@Primary='true']/DocumentedName/
                              DocumentedNamePart/NamePartValue (first primary alias)

          Pass 3 — SanctionsEntries:
            SanctionsEntry[@ProfileID] links to Profile[@ID].
            Program name is in SanctionsMeasure[@SanctionsTypeID='1']/Comment.

        Returns:
          Address index: {lowercase_address: {name, sdn_id, currency, program, address}}
        """
        xml_path = self._xml_file()
        if not xml_path.exists():
            raise FileNotFoundError(f"OFAC XML not found at {xml_path}. Run download() first.")

        logger.info("Parsing OFAC SDN XML for digital currency addresses ...")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        t = self._t

        # ------ Pass 1: Feature type ID → currency symbol ------
        # "Digital Currency Address - ETH" → feature_type_id: "ETH"
        crypto_types: dict[str, str] = {}
        for ft in root.iter(t("FeatureType")):
            ft_id = ft.get("ID", "")
            text = (ft.text or "").strip()
            if "Digital Currency Address" in text:
                symbol = text.split(" - ", 1)[-1].strip() if " - " in text else text
                crypto_types[ft_id] = symbol

        logger.info(
            f"Found {len(crypto_types)} digital currency feature types: "
            f"{sorted(set(crypto_types.values()))}"
        )

        # ------ Pass 2: DistinctParties → addresses + primary name per profile ------
        # Structure:
        #   DistinctParty[@FixedRef]
        #     Profile[@ID]
        #       Identity
        #         Alias[@Primary='true']
        #           DocumentedName[@DocNameStatusID='1']  (primary, current name)
        #             DocumentedNamePart
        #               NamePartValue  ← entity name text
        #       Feature[@FeatureTypeID]  (for crypto addresses)
        #         FeatureVersion
        #           VersionDetail  ← wallet address text
        profile_addrs: dict[str, list[dict]] = {}   # {profile_id: [{currency, address}]}
        profile_names: dict[str, str] = {}           # {profile_id: entity_name}

        for party in root.iter(t("DistinctParty")):
            for profile in party.iter(t("Profile")):
                pid = profile.get("ID", "")

                # Extract primary name (first primary alias, current status)
                name = ""
                for identity in profile.iter(t("Identity")):
                    for alias in identity:
                        if alias.tag != t("Alias"):
                            continue
                        if alias.get("Primary", "").lower() != "true":
                            continue
                        # Take the first DocumentedName with DocNameStatusID='1' (current)
                        for doc_name in alias:
                            if doc_name.tag != t("DocumentedName"):
                                continue
                            if doc_name.get("DocNameStatusID") != "1":
                                continue
                            parts: list[str] = []
                            for part in doc_name.iter(t("NamePartValue")):
                                val = (part.text or "").strip()
                                if val:
                                    parts.append(val)
                            if parts:
                                name = " ".join(parts)
                                break
                        if name:
                            break
                    if name:
                        break
                if name:
                    profile_names[pid] = name

                # Extract crypto addresses
                addrs: list[dict] = []
                for feature in profile:
                    # Features are direct children of Profile (not nested deeper)
                    if feature.tag != t("Feature"):
                        continue
                    ft_id = feature.get("FeatureTypeID", "")
                    if ft_id not in crypto_types:
                        continue
                    currency = crypto_types[ft_id]
                    for version in feature.iter(t("FeatureVersion")):
                        for detail in version.iter(t("VersionDetail")):
                            addr = (detail.text or "").strip()
                            if addr:
                                addrs.append({"currency": currency, "address": addr})
                if addrs:
                    profile_addrs[pid] = addrs

        logger.info(f"Found {len(profile_addrs)} profiles with digital currency addresses")

        # ------ Pass 3: SanctionsEntries → program per profile ------
        # SanctionsEntry[@ProfileID] → SanctionsMeasure[@SanctionsTypeID='1']/Comment
        # SanctionsTypeID='1' is the program designation measure.
        profile_program: dict[str, str] = {}

        for se in root.iter(t("SanctionsEntry")):
            pid = se.get("ProfileID", "")
            if not pid:
                continue
            program = ""
            for measure in se.iter(t("SanctionsMeasure")):
                if measure.get("SanctionsTypeID") == "1":
                    comment_el = measure.find(t("Comment"))
                    if comment_el is not None and comment_el.text:
                        program = comment_el.text.strip()
                        break
            if program:
                profile_program[pid] = program

        # ------ Join: build final address index ------
        index: dict[str, dict] = {}
        for pid, addrs in profile_addrs.items():
            name = profile_names.get(pid, "")
            program = profile_program.get(pid, "")
            for addr_info in addrs:
                key = addr_info["address"].lower()
                index[key] = {
                    "name": name,
                    "sdn_id": pid,
                    "currency": addr_info["currency"],
                    "program": program,
                    "address": addr_info["address"],
                }

        logger.info(f"OFAC parse complete: {len(index)} digital currency addresses indexed")
        return index

    # ------------------------------------------------------------------
    # Cache I/O
    # ------------------------------------------------------------------

    def _save_index(self, index: dict) -> None:
        self._index_file().write_text(json.dumps(index))

    def _load_index_from_cache(self) -> dict | None:
        f = self._index_file()
        if f.exists():
            try:
                return json.loads(f.read_text())
            except Exception:
                return None
        return None

    # ------------------------------------------------------------------
    # Public: refresh / load / check
    # ------------------------------------------------------------------

    def refresh(self, force: bool = False) -> bool:
        """
        Download and re-parse the OFAC SDN list.

        Args:
            force: Ignore staleness check and always re-download.

        Returns:
            True on success. False if download fails (existing cache remains active).
        """
        if not force and not self._is_stale():
            logger.info("OFAC data is fresh — skipping refresh")
            return True

        if not self.download():
            logger.warning("OFAC download failed — will continue with cached data")
            return False

        try:
            index = self.parse()
            self._save_index(index)
            self._index = index
            self._loaded = True
            self._write_meta(
                {
                    "last_updated": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                    "address_count": len(index),
                }
            )
            logger.info(f"OFAC refresh complete: {len(index)} addresses indexed")
            return True
        except Exception as exc:
            logger.error(f"OFAC parse error: {exc}")
            return False

    def load(self) -> None:
        """
        Load the screener, using cache when available and fresh.

        Called lazily on first check(). Safe to call multiple times.
        On a cold start (no cache): downloads + parses (~2-3 min).
        On a warm start (fresh cache): loads JSON index (~1 sec).
        """
        if self._loaded:
            return

        # Fast path: cached index is fresh
        if not self._is_stale():
            cached = self._load_index_from_cache()
            if cached is not None:
                self._index = cached
                self._loaded = True
                logger.info(f"Loaded OFAC index from cache: {len(cached)} addresses")
                return

        # Slow path: need fresh data
        self.refresh()

        # Fail-safe: if refresh failed, fall back to stale cache rather than
        # running with no sanctions data at all
        if not self._loaded:
            cached = self._load_index_from_cache()
            if cached is not None:
                self._index = cached
                self._loaded = True
                logger.warning(
                    f"Using stale OFAC cache (refresh failed): {len(cached)} addresses"
                )
            else:
                # No data at all — log loudly but don't crash the API
                logger.error(
                    "OFAC screener has no data. Sanctions screening is DEGRADED. "
                    "Run `python -m app.services.ofac` to manually download."
                )

    def check(self, wallet: str) -> SanctionsMatch:
        """
        Check if a wallet address is on the OFAC SDN list.

        Args:
            wallet: Wallet address string (any casing, any chain).

        Returns:
            SanctionsMatch. matched=True means the address is sanctioned.
        """
        if not wallet:
            return SanctionsMatch(matched=False)

        if not self._loaded:
            self.load()

        entry = self._index.get(wallet.lower().strip())
        if entry:
            return SanctionsMatch(
                matched=True,
                name=entry.get("name", ""),
                sdn_id=entry.get("sdn_id", ""),
                currency=entry.get("currency", ""),
                program=entry.get("program", ""),
                list_source="OFAC_SDN",
            )

        return SanctionsMatch(matched=False)

    # ------------------------------------------------------------------
    # Status / introspection
    # ------------------------------------------------------------------

    @property
    def address_count(self) -> int:
        return len(self._index)

    @property
    def last_updated(self) -> Optional[str]:
        return self._read_meta().get("last_updated")

    def status(self) -> dict:
        return {
            "loaded": self._loaded,
            "address_count": self.address_count,
            "last_updated": self.last_updated,
            "data_stale": self._is_stale(),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_screener: Optional[OFACScreener] = None


def get_screener() -> OFACScreener:
    """
    Return the module-level OFACScreener singleton.

    Initialised on first call using values from app.core.config.settings
    so that OFAC_SDN_URL / OFAC_UPDATE_INTERVAL_HOURS / OFAC_DATA_DIR env
    vars are respected without importing config at module load time.
    """
    global _screener
    if _screener is None:
        try:
            from app.core.config import settings

            _screener = OFACScreener(
                data_dir=settings.ofac_data_dir,
                refresh_hours=settings.ofac_update_interval_hours,
            )
            # Override the download URL from config
            _screener._sdn_url = settings.ofac_sdn_url
        except ImportError:
            # Fallback for use outside the FastAPI app (e.g. CLI, tests)
            _screener = OFACScreener()
    return _screener


# ---------------------------------------------------------------------------
# CLI entrypoint: python -m app.services.ofac
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    force = "--force" in sys.argv
    screener = OFACScreener()
    ok = screener.refresh(force=force)

    if ok:
        print(f"\nOFAC index built: {screener.address_count} digital currency addresses")
        print(f"Stored at: {screener._index_file()}")
    else:
        print("\nFailed to refresh OFAC data. Check logs above.", file=sys.stderr)
        sys.exit(1)
