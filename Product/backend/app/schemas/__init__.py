"""
Pydantic schemas for API request/response models.

Organized by domain for clarity.
"""

from .common import Entity
from .transactions import (
    AuditApproval,
    AuditRecord,
    PaymentAnnotateRequest,
    PaymentAnnotateResponse,
    TransactionIngestRequest,
    TransactionIngestResponse,
    TransactionListResponse,
    TransactionSummary,
    TravelRuleInfo,
)
from .wallets import (
    WalletProof,
    WalletVerifyRequest,
    WalletVerifyResponse,
)
from .travel_rule import (
    TravelRuleTransmitRequest,
    TravelRuleTransmitResponse,
)
from .reports import ReportExportResponse
from .api_keys import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyInfo,
    APIKeyListResponse,
    APIKeyRevokeResponse,
)
from .signup import SignupRequest, SignupResponse, TallyWebhookPayload

__all__ = [
    # Common
    "Entity",
    # Transactions
    "AuditApproval",
    "AuditRecord",
    "PaymentAnnotateRequest",
    "PaymentAnnotateResponse",
    "TransactionIngestRequest",
    "TransactionIngestResponse",
    "TransactionListResponse",
    "TransactionSummary",
    "TravelRuleInfo",
    # Wallets
    "WalletProof",
    "WalletVerifyRequest",
    "WalletVerifyResponse",
    # Travel Rule
    "TravelRuleTransmitRequest",
    "TravelRuleTransmitResponse",
    # Reports
    "ReportExportResponse",
    # API Keys
    "APIKeyCreateRequest",
    "APIKeyCreateResponse",
    "APIKeyInfo",
    "APIKeyListResponse",
    "APIKeyRevokeResponse",
    # Signup
    "SignupRequest",
    "SignupResponse",
    "TallyWebhookPayload",
]
