"""
Report export schemas.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class ReportExportResponse(BaseModel):
    """Response when exporting a report."""
    report_id: str
    status: Literal["ready", "processing"]
    download_url: Optional[str] = None
    expires_at: Optional[str] = None
