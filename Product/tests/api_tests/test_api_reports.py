"""
Integration tests for GET /v1/reports/export.

Tests:
  - CSV export with no records → headers-only CSV
  - CSV export with records → data rows present
  - JSON export with no records → empty list
  - JSON export with records → populated list
  - Date range filtering excludes records outside the range
  - Auth required
"""

import csv
import io

EXPORT_URL   = "/v1/reports/export"
INGEST_URL   = "/v1/transactions/ingest"


def _ingest(client, auth_headers, sample_transaction, external_id=None):
    """Ingest a transaction and return the response JSON."""
    payload = dict(sample_transaction)
    if external_id:
        payload["external_id"] = external_id
    resp = client.post(INGEST_URL, json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


class TestCSVExport:

    def test_empty_csv_has_headers(self, client, auth_headers):
        """With no transactions, the CSV must still contain the header row."""
        resp = client.get(EXPORT_URL, params={"format": "csv"}, headers=auth_headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) >= 1, "Expected at least a header row"
        headers = rows[0]
        assert "transaction_id" in headers
        assert "risk_level" in headers
        assert "sanctions_result" in headers

    def test_csv_has_data_row_after_ingest(self, client, auth_headers, sample_transaction):
        _ingest(client, auth_headers, sample_transaction)
        resp = client.get(EXPORT_URL, params={"format": "csv"}, headers=auth_headers)
        assert resp.status_code == 200

        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["risk_level"] == "low"
        assert rows[0]["sanctions_result"] == "passed"

    def test_csv_only_includes_own_business_records(
        self, client, auth_headers, sample_transaction
    ):
        """Records from another business must not appear in the export."""
        _ingest(client, auth_headers, sample_transaction)

        other_headers = {"X-API-Key": "sk_test_globalcorp_789012"}
        resp = client.get(EXPORT_URL, params={"format": "csv"}, headers=other_headers)
        assert resp.status_code == 200

        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 0  # globalcorp has no transactions


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


class TestJSONExport:

    def test_empty_json_export(self, client, auth_headers):
        resp = client.get(EXPORT_URL, params={"format": "json"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["records"] == []
        assert data["count"] == 0

    def test_json_export_with_records(self, client, auth_headers, sample_transaction):
        _ingest(client, auth_headers, sample_transaction)
        resp = client.get(EXPORT_URL, params={"format": "json"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert len(data["records"]) == 1
        record = data["records"][0]
        assert record["asset"] == "USDC"
        assert record["sanctions_result"] == "passed"

    def test_json_export_multiple_records(self, client, auth_headers, sample_transaction):
        _ingest(client, auth_headers, sample_transaction, external_id="exp-001")
        payload2 = dict(sample_transaction)
        payload2["external_id"] = "exp-002"
        payload2["amount"] = "1500.00"
        client.post(INGEST_URL, json=payload2, headers=auth_headers)

        resp = client.get(EXPORT_URL, params={"format": "json"}, headers=auth_headers)
        data = resp.json()
        assert data["count"] == 2


# ---------------------------------------------------------------------------
# Date range filtering
# ---------------------------------------------------------------------------


class TestDateRangeFilter:
    """from_date / to_date query params filter the result set."""

    def test_future_from_date_returns_empty(self, client, auth_headers, sample_transaction):
        """Records created today should not appear if from_date is tomorrow."""
        _ingest(client, auth_headers, sample_transaction)
        resp = client.get(
            EXPORT_URL,
            params={"format": "json", "from_date": "2099-01-01"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_past_to_date_returns_empty(self, client, auth_headers, sample_transaction):
        """Records created today should not appear if to_date is yesterday."""
        _ingest(client, auth_headers, sample_transaction)
        resp = client.get(
            EXPORT_URL,
            params={"format": "json", "to_date": "2000-01-01"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_wide_date_range_includes_records(self, client, auth_headers, sample_transaction):
        """A date range spanning today must include today's records."""
        _ingest(client, auth_headers, sample_transaction)
        resp = client.get(
            EXPORT_URL,
            params={"format": "json", "from_date": "2020-01-01", "to_date": "2099-12-31"},
            headers=auth_headers,
        )
        assert resp.json()["count"] == 1


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestExportAuth:

    def test_export_requires_auth(self, client):
        resp = client.get(EXPORT_URL, params={"format": "csv"})
        assert resp.status_code == 401

    def test_invalid_format_returns_422(self, client, auth_headers):
        resp = client.get(EXPORT_URL, params={"format": "xml"}, headers=auth_headers)
        assert resp.status_code == 422
