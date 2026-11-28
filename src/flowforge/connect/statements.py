"""Bank statement files: CSV exports and OFX/QFX (Quicken / QuickBooks web connect).

Every bank offers one of these downloads, so statement import works for any bank, with
no API keys. Amounts are returned in FlowForge's convention: positive = money out.
"""

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class StatementLine:
    external_id: str
    posted: date
    amount: Decimal  # positive = money out of the account
    description: str


@dataclass(slots=True)
class Statement:
    lines: list[StatementLine]
    account_number: str | None = None
    currency: str | None = None
    balance: Decimal | None = None
    balance_date: date | None = None


_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%b %d, %Y",
    "%Y/%m/%d",
    "%m-%d-%Y",
    "%Y%m%d",
)


def parse_date(text: str) -> date:
    text = text.strip()
    # Accept a trailing time ("2026-11-03 14:22", "2026-11-03T14:22:00").
    candidates = [text, re.split(r"[ T]", text, maxsplit=1)[0]] if text else []
    for candidate in candidates:
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Unrecognised date: {text[:30]}")


def parse_amount(text: str) -> Decimal | None:
    raw = text.strip()
    if not raw:
        return None
    negative = raw.startswith("(") and raw.endswith(")") or raw.endswith("-") or "-" in raw[:2]
    cleaned = re.sub(r"[^0-9.]", "", raw)
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Unrecognised amount: {raw[:30]}") from exc
    return -value if negative else value


def _key(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


_DATE_COLUMNS = (
    "date",
    "postingdate",
    "posteddate",
    "transactiondate",
    "postdate",
    "effectivedate",
)
_DESC_COLUMNS = ("description", "memo", "payee", "name", "details", "transaction", "narrative")
_AMOUNT_COLUMNS = ("amount", "transactionamount", "amountusd", "value")
_OUT_COLUMNS = ("debit", "withdrawal", "withdrawals", "debitamount", "moneyout", "paidout")
_IN_COLUMNS = ("credit", "deposit", "deposits", "creditamount", "moneyin", "paidin")
_BALANCE_COLUMNS = ("balance", "runningbalance", "availablebalance")


def _pick(columns: dict[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in columns:
            return columns[name]
    return None


def parse_csv(text: str) -> Statement:
    rows = list(csv.reader(io.StringIO(text)))
    # Some banks put account details above the header row: find the header.
    header_index = next(
        (
            i
            for i, row in enumerate(rows[:15])
            if any(_key(c) in _DATE_COLUMNS for c in row)
            and any(_key(c) in _AMOUNT_COLUMNS + _OUT_COLUMNS + _IN_COLUMNS for c in row)
        ),
        None,
    )
    if header_index is None:
        raise ValueError(
            "Could not find the columns. The file needs a header row with a date column and "
            "an amount column (or debit and credit columns)."
        )
    header = rows[header_index]
    columns = {_key(c): c for c in header}
    index = {c: i for i, c in enumerate(header)}
    date_col = _pick(columns, _DATE_COLUMNS)
    desc_col = _pick(columns, _DESC_COLUMNS)
    amount_col = _pick(columns, _AMOUNT_COLUMNS)
    out_col = _pick(columns, _OUT_COLUMNS)
    in_col = _pick(columns, _IN_COLUMNS)
    balance_col = _pick(columns, _BALANCE_COLUMNS)
    assert date_col is not None
    lines: list[StatementLine] = []
    seen: dict[str, int] = {}
    balance: Decimal | None = None
    balance_date: date | None = None
    for number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if not any(cell.strip() for cell in row):
            continue

        def cell(col: str | None, r: list[str] = row) -> str:
            return r[index[col]] if col is not None and index[col] < len(r) else ""

        try:
            posted = parse_date(cell(date_col))
        except ValueError as exc:
            raise ValueError(f"Row {number}: {exc}") from exc
        if amount_col:
            value = parse_amount(cell(amount_col))
            if value is None:
                continue
            amount = -value  # statements show deposits positive; FlowForge: positive = out
        else:
            out = parse_amount(cell(out_col)) or Decimal("0")
            inn = parse_amount(cell(in_col)) or Decimal("0")
            if out == 0 and inn == 0:
                continue
            amount = abs(out) - abs(inn)
        description = (cell(desc_col) or "Bank transaction").strip()[:500]
        if balance_col:
            b = parse_amount(cell(balance_col))
            if b is not None and (balance_date is None or posted >= balance_date):
                balance, balance_date = b, posted
        base = f"{posted.isoformat()}|{amount}|{description.lower()}"
        seen[base] = seen.get(base, 0) + 1
        digest = hashlib.sha256(f"{base}|{seen[base]}".encode()).hexdigest()[:40]
        lines.append(StatementLine(f"csv-{digest}", posted, amount, description))
    if not lines:
        raise ValueError("The file has no transactions")
    return Statement(lines, balance=balance, balance_date=balance_date)


def _ofx_value(block: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>([^<\r\n]*)", block, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_ofx(text: str) -> Statement:
    blocks = re.findall(
        r"<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|(?=</BANKTRANLIST>))", text, re.S | re.I
    )
    lines: list[StatementLine] = []
    for block in blocks:
        amount_text = _ofx_value(block, "TRNAMT")
        posted_text = _ofx_value(block, "DTPOSTED")
        if not amount_text or not posted_text:
            continue
        value = parse_amount(amount_text)
        if value is None:
            continue
        posted = datetime.strptime(posted_text[:8], "%Y%m%d").date()
        name = _ofx_value(block, "NAME") or ""
        memo = _ofx_value(block, "MEMO") or ""
        description = (
            name + (" — " + memo if memo and memo != name else "")
        ).strip() or "Bank transaction"
        fitid = (
            _ofx_value(block, "FITID")
            or hashlib.sha256(f"{posted}|{value}|{description}".encode()).hexdigest()[:40]
        )
        lines.append(StatementLine(f"ofx-{fitid[:150]}", posted, -value, description[:500]))
    if not lines:
        raise ValueError("The OFX/QFX file has no transactions")
    ledger = re.search(r"<LEDGERBAL>(.*?)(?:</LEDGERBAL>|<AVAILBAL>|</STMTRS>)", text, re.S | re.I)
    balance = balance_date = None
    if ledger:
        amount = _ofx_value(ledger.group(1), "BALAMT")
        when = _ofx_value(ledger.group(1), "DTASOF")
        balance = parse_amount(amount) if amount else None
        balance_date = datetime.strptime(when[:8], "%Y%m%d").date() if when else None
    account = _ofx_value(text, "ACCTID")
    return Statement(
        lines,
        account_number=account,
        currency=(_ofx_value(text, "CURDEF") or None),
        balance=balance,
        balance_date=balance_date,
    )


def parse_statement(filename: str, data: bytes) -> Statement:
    text = data.decode("utf-8-sig", errors="replace")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("ofx", "qfx") or "<OFX>" in text[:5000].upper():
        return parse_ofx(text)
    if ext in ("csv", "txt"):
        return parse_csv(text)
    raise ValueError(
        "Upload the statement as CSV, OFX or QFX (download it from your bank's website)"
    )
