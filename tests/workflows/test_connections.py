"""Connections release: uploads in every section, bank feeds (Plaid, statements, demo),
shipping carrier tracking (FedEx, UPS, USPS, DHL, demo) and payroll migration (files and
Gusto). Provider APIs are replaced by httpx.MockTransport with their documented shapes."""

import json
from collections.abc import Callable, Iterator
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
import pytest

from flowforge.connect import http as provider_http
from flowforge.core.config import settings

from . import payroll_helpers as ph
from .conftest import Harness

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def mock_providers() -> Iterator[Callable[[Callable[[httpx.Request], httpx.Response]], list[httpx.Request]]]:
    seen: list[httpx.Request] = []

    def install(handler: Callable[[httpx.Request], httpx.Response]) -> list[httpx.Request]:
        def record(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request)

        provider_http.TRANSPORT = httpx.MockTransport(record)
        return seen

    yield install
    provider_http.TRANSPORT = None


async def _upload(h: Harness, path: str, filename: str, data: bytes, headers: dict[str, str] | None = None,
                  **form: str) -> httpx.Response:
    return await h.client.post(path, headers=headers or h.owner, files={"file": (filename, data)}, data=form)


async def _viewer(h: Harness) -> dict[str, str]:
    email = f"viewer-{uuid4().hex[:8]}@example.com"
    password = f"View-{uuid4().hex}"
    await h.post("/api/v1/users", json={"email": email, "display_name": "Viewer", "password": password,
                                        "roles": ["Viewer"]})
    slug = (await h.sql("SELECT slug FROM tenants WHERE id = :t", t=str(h.tenant_id)))[0][0]
    login = await h.client.post("/api/v1/auth/login", json={"email": email, "password": password, "tenant_slug": slug})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ------------------------------------------------------------------ uploads
async def test_upload_list_download_delete(harness: Harness) -> None:
    h = harness
    made = await _upload(h, "/api/v1/files", "invoice-1001.pdf", PDF, section="payables",
                         record_type="vendor_invoice", record_id="INV-1001", note="March invoice")
    assert made.status_code == 201, made.text
    file = made.json()
    assert file["content_type"] == "application/pdf" and file["size_bytes"] == len(PDF)

    listed = await h.call("GET", "/api/v1/files", params={"section": "payables"})
    assert [f["id"] for f in listed] == [file["id"]]
    assert await h.call("GET", "/api/v1/files", params={"section": "payroll"}) == []

    download = await h.client.get(f"/api/v1/files/{file['id']}/content", headers=h.owner)
    assert download.status_code == 200 and download.content == PDF
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "invoice-1001.pdf" in download.headers["content-disposition"]

    # Active content and disguised files are refused.
    for name, data in (("page.html", b"<script>alert(1)</script>"), ("fake.pdf", b"<html>"),
                       ("empty.pdf", b""), ("x.svg", b"<svg/>")):
        refused = await _upload(h, "/api/v1/files", name, data, section="payables")
        assert refused.status_code == 409, (name, refused.text)

    # A viewer can read but not upload or delete.
    viewer = await _viewer(h)
    assert (await h.client.get("/api/v1/files", headers=viewer)).status_code == 200
    assert (await _upload(h, "/api/v1/files", "a.pdf", PDF, headers=viewer, section="ap")).status_code == 403
    assert (await h.client.delete(f"/api/v1/files/{file['id']}", headers=viewer)).status_code == 403

    await h.call("DELETE", f"/api/v1/files/{file['id']}", expect=204)
    assert await h.call("GET", "/api/v1/files") == []
    gone = await h.client.get(f"/api/v1/files/{file['id']}/content", headers=h.owner)
    assert gone.status_code == 404


async def test_another_tenant_cannot_see_our_files(harness: Harness) -> None:
    h = harness
    file = (await _upload(h, "/api/v1/files", "contract.pdf", PDF, section="documents")).json()
    slug = f"other-{uuid4().hex[:8]}"
    created = await h.client.post("/api/v1/auth/bootstrap", json={
        "tenant": {"name": "Other", "slug": slug}, "email": f"o-{slug}@example.com",
        "password": f"Other-{uuid4().hex}", "display_name": "Other"})
    other = {"Authorization": f"Bearer {created.json()['access_token']}"}
    other_tenant = (await h.client.get("/api/v1/me", headers=other)).json()["tenant_id"]
    try:
        assert (await h.client.get(f"/api/v1/files/{file['id']}/content", headers=other)).status_code == 404
        assert (await h.client.get("/api/v1/files", headers=other)).json() == []
    finally:
        from sqlalchemy import text

        from flowforge.db.session import engine
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM tenants WHERE id = :i"), {"i": other_tenant})


# ------------------------------------------------------------------ banking
async def test_demo_bank_and_statement_imports(harness: Harness) -> None:
    h = harness
    assert (await h.post("/api/v1/banking/link", json={"provider": "demo"}))["link_token"] == "demo-link"
    connected = await h.post("/api/v1/banking/connections",
                             json={"provider": "demo", "public_token": "demo-link"})
    assert connected["accounts"] == 3 and connected["transactions_added"] == 10
    again = await h.post(f"/api/v1/banking/connections/{connected['connection_id']}/sync")
    assert again["transactions_added"] == 0

    overview = await h.call("GET", "/api/v1/banking/overview")
    names = {a["name"]: a for a in overview["accounts"]}
    assert names["Business Checking (demo)"]["current_balance"] == "48250.17"
    assert overview["totals"] == [{"currency": "USD", "cash": "173250.17", "owed": "3210.45"}]
    payment = next(t for t in await h.call("GET", "/api/v1/banking/transactions", params={"search": "Acme"}))
    assert payment["money_in"] == "18450.00" and payment["money_out"] is None

    # Any bank: CSV statement with debit/credit columns and a header block above it.
    csv_text = ("Account,Operating 9911\n\nPosting Date,Description,Debit,Credit,Balance\n"
                "11/03/2026,Deposit — Initech,,2500.00,10500.00\n"
                "11/04/2026,Check 1042,120.50,,10379.50\n"
                "11/04/2026,Check 1042,120.50,,10259.00\n")
    imported = (await _upload(h, "/api/v1/banking/statements", "nov.csv", csv_text.encode(),
                              account_name="Operating at First Bank")).json()
    assert imported["transactions_added"] == 3 and imported["balance"] == "10259.00", imported
    account_id = imported["account_id"]
    repeat = (await _upload(h, "/api/v1/banking/statements", "nov.csv", csv_text.encode(),
                            account_id=account_id)).json()
    assert repeat["transactions_added"] == 0 and repeat["transactions_already_imported"] == 3
    rows = await h.call("GET", "/api/v1/banking/transactions", params={"account_id": account_id})
    assert sorted(r["money_out"] or r["money_in"] for r in rows) == ["120.50", "120.50", "2500.00"]
    # Each imported statement file is kept in the banking section.
    assert [f["filename"] for f in await h.call("GET", "/api/v1/files", params={"section": "banking"})] == ["nov.csv"] * 2

    ofx = """OFXHEADER:100
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>USD<BANKACCTFROM><ACCTID>000123456789</BANKACCTFROM>
<BANKTRANLIST><STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20261105120000<TRNAMT>-45.10<FITID>A1<NAME>Coffee Co
</STMTTRN><STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20261106<TRNAMT>900.00<FITID>A2<NAME>Refund</STMTTRN>
</BANKTRANLIST><LEDGERBAL><BALAMT>5000.00<DTASOF>20261106</LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"""
    ofx_result = (await _upload(h, "/api/v1/banking/statements", "nov.qfx", ofx.encode(),
                                account_name="Savings")).json()
    assert ofx_result["transactions_added"] == 2 and ofx_result["balance"] == "5000.00"
    savings = next(a for a in (await h.call("GET", "/api/v1/banking/overview"))["accounts"] if a["name"] == "Savings")
    assert savings["mask"] == "6789"

    bad = await _upload(h, "/api/v1/banking/statements", "x.csv", b"hello,world\n1,2\n", account_name="X")
    assert bad.status_code == 409 and "columns" in bad.text

    await h.call("DELETE", f"/api/v1/banking/connections/{connected['connection_id']}", expect=204)
    remaining = {a["name"] for a in (await h.call("GET", "/api/v1/banking/overview"))["accounts"]}
    assert "Business Checking (demo)" not in remaining and "Savings" in remaining


async def test_plaid_connection_syncs_and_keeps_token_encrypted(
    harness: Harness, mock_providers: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness
    refused = await h.post("/api/v1/banking/link", json={"provider": "plaid"}, expect=409)
    assert "not set up" in json.dumps(refused)

    monkeypatch.setattr(settings, "plaid_client_id", "client-123")
    monkeypatch.setattr(settings, "plaid_secret", "secret-456")
    access_token = f"access-sandbox-{uuid4().hex}"
    cursor_calls: list[Any] = []

    def plaid(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["client_id"] == "client-123" and body["secret"] == "secret-456"
        assert request.url.host == "sandbox.plaid.com"
        path = request.url.path
        if path == "/link/token/create":
            assert body["products"] == ["transactions"]
            return httpx.Response(200, json={"link_token": "link-sandbox-abc"})
        if path == "/item/public_token/exchange":
            assert body["public_token"] == "public-sandbox-xyz"
            return httpx.Response(200, json={"access_token": access_token, "item_id": "item-1"})
        if path == "/accounts/get":
            return httpx.Response(200, json={"accounts": [{
                "account_id": "acc-1", "name": "Plaid Checking", "official_name": "Plaid Gold Checking",
                "mask": "0000", "type": "depository", "subtype": "checking",
                "balances": {"current": 110.5, "available": 100, "iso_currency_code": "USD"}}]})
        if path == "/transactions/sync":
            cursor_calls.append(body.get("cursor"))
            if body.get("cursor") is None:
                return httpx.Response(200, json={"added": [
                    {"transaction_id": "t1", "account_id": "acc-1", "amount": 89.4, "date": "2026-11-20",
                     "name": "UNITED AIRLINES", "merchant_name": "United Airlines", "pending": False,
                     "iso_currency_code": "USD"},
                    {"transaction_id": "t2", "account_id": "acc-1", "amount": -500, "date": "2026-11-21",
                     "name": "INTRST PYMNT", "pending": False, "iso_currency_code": "USD"}],
                    "modified": [], "removed": [], "next_cursor": "c1", "has_more": False})
            return httpx.Response(200, json={"added": [], "modified": [], "removed": [{"transaction_id": "t1"}],
                                             "next_cursor": "c2", "has_more": False})
        if path == "/item/remove":
            return httpx.Response(200, json={"removed": True})
        return httpx.Response(404, json={"error_message": "unexpected"})

    mock_providers(plaid)
    assert (await h.post("/api/v1/banking/link", json={"provider": "plaid"}))["link_token"] == "link-sandbox-abc"
    connected = await h.post("/api/v1/banking/connections", json={
        "provider": "plaid", "public_token": "public-sandbox-xyz", "institution_name": "First Platypus Bank"})
    assert connected["transactions_added"] == 2
    stored = await h.sql("SELECT encrypted_access_token FROM bank_connections WHERE id = :i",
                         i=connected["connection_id"])
    assert stored[0][0].startswith("ffc2:") and access_token not in stored[0][0]

    tx = await h.call("GET", "/api/v1/banking/transactions")
    assert {t["description"]: (t["money_out"], t["money_in"]) for t in tx} == {
        "United Airlines": ("89.40", None), "INTRST PYMNT": (None, "500.00")}
    synced = await h.post(f"/api/v1/banking/connections/{connected['connection_id']}/sync")
    assert synced["transactions_removed"] == 1 and cursor_calls == [None, "c1"]
    assert [t["description"] for t in await h.call("GET", "/api/v1/banking/transactions")] == ["INTRST PYMNT"]
    await h.call("DELETE", f"/api/v1/banking/connections/{connected['connection_id']}", expect=204)
    assert (await h.sql("SELECT encrypted_access_token, status FROM bank_connections WHERE id = :i",
                        i=connected["connection_id"]))[0] == (None, "disconnected")


# ------------------------------------------------------------------ shipping
def _carrier_api(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url.endswith("/oauth/token") or url.endswith("/oauth2/v3/token") or "security/v1/oauth/token" in url:
        if b"bad-secret" in request.content or "YmFkLWlkOmJhZC1zZWNyZXQ" in request.headers.get("authorization", ""):
            return httpx.Response(401, json={"errors": [{"code": "NOT.AUTHORIZED", "message": "Invalid credentials"}]})
        return httpx.Response(200, json={"access_token": "carrier-token", "expires_in": 3600})
    assert request.headers.get("authorization") == "Bearer carrier-token" or "DHL-API-Key" in request.headers
    if "fedex.com/track" in url:
        return httpx.Response(200, json={"output": {"completeTrackResults": [{"trackResults": [{
            "latestStatusDetail": {"code": "DL", "description": "Delivered",
                                   "scanLocation": {"city": "MEMPHIS", "stateOrProvinceCode": "TN"}},
            "dateAndTimes": [{"type": "ACTUAL_DELIVERY", "dateTime": "2026-11-25T10:02:00-06:00"}],
            "scanEvents": [
                {"date": "2026-11-25T10:02:00-06:00", "eventDescription": "Delivered", "eventType": "DL",
                 "scanLocation": {"city": "MEMPHIS", "stateOrProvinceCode": "TN", "countryCode": "US"}},
                {"date": "2026-11-24T08:00:00-06:00", "eventDescription": "On the way", "eventType": "IT",
                 "scanLocation": {"city": "DALLAS", "stateOrProvinceCode": "TX", "countryCode": "US"}}]}]}]}})
    if "/api/track/v1/details/" in url:
        return httpx.Response(200, json={"trackResponse": {"shipment": [{"package": [{
            "currentStatus": {"code": "I", "description": "On the Way"},
            "deliveryDate": [{"type": "SDD", "date": "20261130"}],
            "activity": [{"location": {"address": {"city": "Louisville", "stateProvince": "KY", "country": "US"}},
                          "status": {"type": "I", "description": "Departed from Facility"},
                          "date": "20261127", "time": "031500"}]}]}]}})
    if "/tracking/v3/tracking/" in url:
        return httpx.Response(200, json={"statusCategory": "Out for Delivery", "statusSummary": "Out for delivery",
                                         "trackingEvents": [{"eventType": "Out for Delivery",
                                                             "eventTimestamp": "2026-11-28T07:10:00Z",
                                                             "eventCity": "AUSTIN", "eventState": "TX"}]})
    if "api-eu.dhl.com" in url:
        if request.url.params.get("trackingNumber") == "0000000000":
            return httpx.Response(404, json={"title": "No shipment with given tracking number found."})
        return httpx.Response(200, json={"shipments": [{"status": {"statusCode": "failure",
                                                                   "description": "Recipient not available"},
                                                        "events": [{"timestamp": "2026-11-27T12:00:00Z",
                                                                    "statusCode": "failure",
                                                                    "description": "Recipient not available",
                                                                    "location": {"address": {"addressLocality": "Leipzig"}}}]}]})
    return httpx.Response(404, json={"message": "unexpected " + url})


async def test_carriers_connect_and_track(harness: Harness, mock_providers: Any) -> None:
    h = harness
    seen = mock_providers(_carrier_api)
    catalog = await h.call("GET", "/api/v1/shipping/carriers")
    assert {c["code"] for c in catalog["carriers"]} == {"fedex", "ups", "usps", "dhl"}

    # Without an account a real carrier's shipment waits with a clear message.
    waiting = await h.post("/api/v1/shipping/shipments", json={"tracking_number": "1Z999AA10123456784",
                                                               "reference": "SO-1001"})
    assert waiting["carrier"] == "ups" and waiting["status"] == "pending"
    assert "Connect your UPS account" in waiting["last_error"]
    assert not seen

    bad = await h.post("/api/v1/shipping/accounts", json={"carrier": "fedex", "credentials": {
        "client_id": "bad-id", "client_secret": "bad-secret"}}, expect=409)
    assert "Invalid credentials" in json.dumps(bad)
    missing = await h.post("/api/v1/shipping/accounts", json={"carrier": "fedex", "credentials": {}}, expect=409)
    assert "API key is required" in json.dumps(missing)

    for carrier, creds in (("fedex", {"client_id": "k", "client_secret": "s", "account_number": "510087020"}),
                           ("ups", {"client_id": "k", "client_secret": "s"}),
                           ("usps", {"client_id": "k", "client_secret": "s"}),
                           ("dhl", {"api_key": "dhl-key"})):
        account = await h.post("/api/v1/shipping/accounts", json={"carrier": carrier, "credentials": creds})
        assert account["status"] == "connected"
    stored = await h.sql("SELECT encrypted_credentials, account_number_mask FROM carrier_accounts WHERE carrier = 'fedex'")
    assert stored[0][0].startswith("ffc2:") and "510087020" not in stored[0][0] and stored[0][1].endswith("7020")

    refreshed = await h.post(f"/api/v1/shipping/shipments/{waiting['id']}/refresh")
    assert refreshed["status"] == "in_transit" and refreshed["estimated_delivery"] == "2026-11-30"
    assert refreshed["last_location"] == "Louisville, KY, US" and refreshed["last_error"] is None

    fedex = await h.post("/api/v1/shipping/shipments", json={"tracking_number": "7946 9876 5432"})
    assert fedex["carrier"] == "fedex" and fedex["status"] == "delivered"
    assert fedex["delivered_at"].startswith("2026-11-25") and len(fedex["events"]) == 2
    usps = await h.post("/api/v1/shipping/shipments", json={"tracking_number": "9400111899223344556677"})
    assert usps["carrier"] == "usps" and usps["status"] == "out_for_delivery"
    dhl = await h.post("/api/v1/shipping/shipments", json={"tracking_number": "1234567890", "carrier": "dhl"})
    assert dhl["status"] == "exception" and dhl["last_location"] == "Leipzig"
    demo = await h.post("/api/v1/shipping/shipments", json={"tracking_number": "DEMO-100"})
    assert demo["carrier"] == "demo" and demo["status"] in ("label_created", "in_transit")

    unknown = await h.post("/api/v1/shipping/shipments", json={"tracking_number": "ABC-XYZ"}, expect=409)
    assert "choose the carrier" in json.dumps(unknown)

    csv_text = "Tracking Number,Carrier,Reference\nDEMO-200,,PO-77\n1Z999AA10123456784,ups,dup\n,,\n"
    bulk = (await _upload(h, "/api/v1/shipping/shipments/import", "track.csv", csv_text.encode())).json()
    assert bulk["added"] == 2 and bulk["failed"] == 0
    listing = await h.call("GET", "/api/v1/shipping/shipments")
    assert len(listing["shipments"]) == 6  # the UPS number is not duplicated
    assert listing["counts"]["delivered"] == 1 and listing["counts"]["exception"] == 1
    active = await h.call("GET", "/api/v1/shipping/shipments", params={"status": "active"})
    assert all(s["status"] != "delivered" for s in active["shipments"])

    viewer = await _viewer(h)
    assert (await h.client.get("/api/v1/shipping/shipments", headers=viewer)).status_code == 200
    denied = await h.client.post("/api/v1/shipping/shipments", headers=viewer, json={"tracking_number": "DEMO-1"})
    assert denied.status_code == 403
    fedex_account = next(a for a in (await h.call("GET", "/api/v1/shipping/carriers"))["accounts"] if a["carrier"] == "fedex")
    await h.call("DELETE", f"/api/v1/shipping/accounts/{fedex_account['id']}", expect=204)
    await h.call("DELETE", f"/api/v1/shipping/shipments/{demo['id']}", expect=204)


# ------------------------------------------------------------------ payroll migration
ADP_EXPORT = """Company Code,ABC
File Number,Legal First Name,Legal Last Name,Work Email,Hire Date,Position Status,Pay Frequency,Regular Pay Rate Amount,Pay Type,Work State,Federal Filing Status,YTD Gross Pay,YTD Federal Income Tax,YTD Social Security,YTD Medicare,YTD Net Pay
000101,Alicia,Moreno,alicia@example.com,03/15/2021,Active,Semimonthly,"78,000.00",Salary,California,Married filing jointly,"68,250.00","7,100.00","4,231.50",989.63,"52,011.87"
000102,Ben,Okafor,ben@example.com,2024-07-01,Active,Semimonthly,32.50,Hourly,TX,Single,"58,110.00","5,020.00","3,602.82",842.60,"47,100.10"
000103,Chris,Lee,,01/02/2019,Terminated,Semimonthly,25.00,Hourly,NY,Single,,,,,
,,,,,,,,,,,,,,,
Total,,,,,,,,,,,"126,360.00",,,,
"""


async def test_payroll_file_migration_and_salary_payroll(harness: Harness) -> None:
    h = harness
    providers = await h.call("GET", "/api/v1/payroll-migration/providers")
    assert {"gusto", "adp_run", "paychex_flex", "quickbooks_payroll", "other"} <= {p["code"] for p in providers["providers"]}

    preview = (await _upload(h, "/api/v1/payroll-migration/preview", "adp.csv", ADP_EXPORT.encode(),
                             provider="adp_run")).json()
    assert preview["count"] == 3 and preview["errors"] == [], preview
    alicia = preview["employees"][0]
    assert (alicia["pay_type"], alicia["pay_rate"], alicia["state"], alicia["pay_frequency"]) == (
        "salary", "78000.00", "CA", "semimonthly")
    assert preview["employees"][2]["status"] == "terminated"

    imported = (await _upload(h, "/api/v1/payroll-migration/file", "adp.csv", ADP_EXPORT.encode(),
                              provider="adp_run", tax_year="2026")).json()
    assert imported["status"] == "completed", imported
    assert imported["summary"]["employees_created"] == 3 and imported["summary"]["ytd_balances"] == 2
    ytd = {r["worker"]: r for r in await h.call("GET", "/api/v1/payroll-migration/ytd", params={"tax_year": 2026})}
    assert ytd["Alicia Moreno"]["gross_pay"] == "68250.00" and ytd["Ben Okafor"]["medicare_tax"] == "842.60"

    # Re-importing updates the same workers (a raise for Ben) instead of duplicating them.
    raised = ADP_EXPORT.replace("32.50,Hourly", "35.00,Hourly")
    again = (await _upload(h, "/api/v1/payroll-migration/file", "adp.csv", raised.encode(),
                           provider="adp_run", tax_year="2026")).json()
    assert again["summary"]["employees_created"] == 0 and again["summary"]["employees_updated"] == 3
    assert again["summary"]["pay_rates_set"] == 1
    workers = await h.sql("SELECT count(*) FROM worker_profiles")
    assert workers[0][0] == 3
    open_rates = await h.sql("SELECT amount FROM compensation_rates WHERE effective_to IS NULL ORDER BY amount")
    assert [Decimal(r[0]) for r in open_rates] == [Decimal("25"), Decimal("35"), Decimal("78000")]

    # The imported salaried worker can be paid by FlowForge: gross = 78,000 / 24.
    alicia_id = (await h.sql("SELECT w.id FROM worker_profiles w JOIN parties p ON p.id = w.party_id"
                             " WHERE p.display_name = 'Alicia Moreno'"))[0][0]
    run_id = await ph.draft_run(h)
    await h.post(f"/api/v4a/payroll/runs/{run_id}/calculate",
                 json={"workers": [{"worker_id": str(alicia_id), "employee_tax_rate": "0.2"}]})
    gross = await h.sql("SELECT gross_pay FROM payroll_run_workers WHERE payroll_run_id = :r", r=run_id)
    assert Decimal(gross[0][0]) == Decimal("3250.00")

    history = await h.call("GET", "/api/v1/payroll-migration/imports")
    assert len(history) == 2 and history[0]["provider_name"] == "ADP RUN"
    files = await h.call("GET", "/api/v1/files", params={"section": "payroll"})
    assert len(files) == 2

    junk = await _upload(h, "/api/v1/payroll-migration/preview", "x.csv", b"a,b\n1,2\n")
    assert junk.status_code == 409 and "employee columns" in junk.text
    viewer = await _viewer(h)
    denied = await h.client.post("/api/v1/payroll-migration/file", headers=viewer,
                                 files={"file": ("a.csv", ADP_EXPORT.encode())})
    assert denied.status_code == 403


async def test_gusto_direct_connection(harness: Harness, mock_providers: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    h = harness
    await h.post("/api/v1/payroll-migration/gusto/start", expect=409)  # not configured
    monkeypatch.setattr(settings, "gusto_client_id", "gusto-client")
    monkeypatch.setattr(settings, "gusto_client_secret", "gusto-secret")

    def gusto(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.gusto-demo.com"
        path = request.url.path
        if path == "/oauth/token":
            body = json.loads(request.content)
            assert body["client_secret"] == "gusto-secret" and body["code"] == "auth-code"
            assert body["redirect_uri"].endswith("/connections/payroll/callback")
            return httpx.Response(200, json={"access_token": "g-access", "refresh_token": "g-refresh", "expires_in": 7200})
        assert request.headers["authorization"] == "Bearer g-access"
        if path == "/v1/token_info":
            return httpx.Response(200, json={"resource": {"type": "Company", "uuid": "co-1"}})
        if path == "/v1/companies/co-1":
            return httpx.Response(200, json={"name": "Wayne Industries LLC", "trade_name": "Wayne Industries"})
        if path == "/v1/companies/co-1/employees":
            if request.url.params.get("page") != "1":
                return httpx.Response(200, json=[])
            return httpx.Response(200, json=[{
                "uuid": "emp-1", "first_name": "Dana", "last_name": "Rivera", "email": "dana@example.com",
                "terminated": False, "start_date": "2023-02-01",
                "jobs": [{"primary": True, "hire_date": "2023-02-01", "location": {"state": "CO"},
                          "compensations": [{"rate": "45.00", "payment_unit": "Hour", "effective_date": "2023-02-01"},
                                            {"rate": "48.00", "payment_unit": "Hour", "effective_date": "2025-01-01"}]}]}])
        if path == "/v1/companies/co-1/payrolls":
            return httpx.Response(200, json=[{"payroll_uuid": "pay-1"}, {"payroll_uuid": "pay-2"}])
        if path.startswith("/v1/companies/co-1/payrolls/"):
            return httpx.Response(200, json={"employee_compensations": [{
                "employee_uuid": "emp-1", "gross_pay": "3840.00", "net_pay": "2900.00",
                "taxes": [{"name": "Federal Income Tax", "employer": False, "amount": "400.00"},
                          {"name": "Social Security", "employer": False, "amount": "238.08"},
                          {"name": "Social Security", "employer": True, "amount": "238.08"},
                          {"name": "Medicare", "employer": False, "amount": "55.68"}],
                "deductions": [{"name": "401k", "amount": "246.24"}]}]})
        return httpx.Response(404, json={"message": "unexpected " + path})

    mock_providers(gusto)
    start = await h.post("/api/v1/payroll-migration/gusto/start")
    assert start["authorize_url"].startswith("https://api.gusto-demo.com/oauth/authorize?client_id=gusto-client")
    state = start["authorize_url"].split("state=")[1]
    await h.post("/api/v1/payroll-migration/gusto/complete", json={"code": "auth-code", "state": "wrong-state-value"}, expect=409)
    connected = await h.post("/api/v1/payroll-migration/gusto/complete", json={"code": "auth-code", "state": state})
    assert connected["status"] == "connected" and connected["company_name"] == "Wayne Industries"
    synced = await h.post(f"/api/v1/payroll-migration/imports/{connected['id']}/sync", json={"tax_year": 2026})
    assert synced["status"] == "completed" and synced["summary"]["employees_created"] == 1
    ytd = (await h.call("GET", "/api/v1/payroll-migration/ytd", params={"tax_year": 2026}))[0]
    assert (ytd["gross_pay"], ytd["federal_income_tax"], ytd["social_security_tax"], ytd["net_pay"]) == (
        "7680.00", "800.00", "476.16", "5800.00")
    rate = await h.sql("SELECT compensation_type, amount FROM compensation_rates")
    assert rate[0][0] == "hourly" and Decimal(rate[0][1]) == Decimal("48")
    tokens = await h.sql("SELECT encrypted_tokens FROM payroll_migrations WHERE id = :i", i=connected["id"])
    assert "g-access" not in tokens[0][0]


async def test_connection_status(harness: Harness) -> None:
    status = await harness.call("GET", "/api/v1/connections/status")
    assert status["banks"] == 0 and status["files"] == 0
    assert status["live_bank_connections_available"] is False
