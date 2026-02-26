"""
Application configuration using environment variables.

All configuration is centralized here for easy management.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Get backend directory (one level up from app/)
BACKEND_DIR = Path(__file__).parent.parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "radius_dev.db"
DEFAULT_OFAC_DATA_DIR = BACKEND_DIR / "data" / "ofac"


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # Environment — controls mock key availability and future debug features
    # "development" enables mock API keys (sk_test_*)
    # "production"  disables mock keys; only DB-backed keys are accepted
    environment: str = "development"

    # Database
    use_database: bool = True
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH}"

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_tokens: int = 100  # Max burst
    rate_limit_refill_rate: float = 1.67  # ~100/min

    # CORS
    allowed_origins: list = None  # type: ignore[assignment]

    # API
    api_version: str = "0.2.0"

    # Sanctions screening
    sanctions_provider: str = "ofac_local"  # "ofac_local" | "opensanctions" (future)
    ofac_sdn_url: str = "https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml"
    ofac_update_interval_hours: int = 24
    ofac_data_dir: Path = field(default_factory=lambda: DEFAULT_OFAC_DATA_DIR)

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        ofac_data_dir_str = os.getenv("OFAC_DATA_DIR", "")
        ofac_data_dir = Path(ofac_data_dir_str) if ofac_data_dir_str else DEFAULT_OFAC_DATA_DIR

        raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

        return cls(
            environment=os.getenv("ENVIRONMENT", "development").lower(),
            allowed_origins=allowed_origins,
            use_database=os.getenv("USE_DATABASE", "true").lower() == "true",
            database_url=os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_tokens=int(os.getenv("RATE_LIMIT_TOKENS", "100")),
            rate_limit_refill_rate=float(os.getenv("RATE_LIMIT_REFILL_RATE", "1.67")),
            api_version=os.getenv("API_VERSION", "0.2.0"),
            sanctions_provider=os.getenv("SANCTIONS_PROVIDER", "ofac_local"),
            ofac_sdn_url=os.getenv(
                "OFAC_SDN_URL",
                "https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml",
            ),
            ofac_update_interval_hours=int(os.getenv("OFAC_UPDATE_INTERVAL_HOURS", "24")),
            ofac_data_dir=ofac_data_dir,
        )


# Global settings instance
settings = Settings.from_env()
