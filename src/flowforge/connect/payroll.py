"""Payroll migration: bring employees, pay rates, tax setup and year-to-date totals over
from the current payroll provider, so FlowForge can run payroll from now on.

Two ways in, both ending in the same import:
* File: every provider (ADP, Paychex, Gusto, QuickBooks, Rippling, Paylocity, ...) can
  export an employee list and a year-to-date payroll report as CSV. Column names differ
  per provider; they are recognised automatically. A preview shows what will be imported.
* Direct connection (Gusto): the user signs in to Gusto (OAuth); FlowForge reads the
  company's employees, compensation and this year's processed payrolls.

Re-importing is safe: workers are matched by their id at the previous provider.
"""

import csv
import io
import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import settings
from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase2a.models import ContactMethod, Party, PartyRoleAssignment, Person
from flowforge.phase2b.models import Currency
from flowforge.phase4a.models import CompensationRate, WorkerProfile, WorkerTaxProfile
from flowforge.platform.numbering import next_number
from flowforge.platform.services import record_change

from . import crypto
from .files import store_file
from .http import ProviderError, request
from .models import PayrollExternalWorker, PayrollMigration, PayrollYtdBalance

router = APIRouter(prefix="/api/v1/payroll-migration", tags=["payroll-migration"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]

GUSTO_HOSTS = {"demo": "https://api.gusto-demo.com", "production": "https://api.gusto.com"}
GUSTO_VERSION = "2024-04-01"


@dataclass(frozen=True, slots=True)
class PayrollProvider:
    code: str
    name: str
    export_steps: str
    api: bool = False


PROVIDERS: dict[str, PayrollProvider] = {
    p.code: p
    for p in (
        PayrollProvider(
            "gusto",
            "Gusto",
            "People → Team members → Export (CSV); Reports → Payroll journal (this year, CSV).",
            api=True,
        ),
        PayrollProvider(
            "adp_run",
            "ADP RUN",
            "Reports → Employee → Employee Details (CSV); Reports → Payroll → Payroll Summary YTD (CSV).",
        ),
        PayrollProvider(
            "adp_workforce_now",
            "ADP Workforce Now",
            "Reports & Analytics → Employee Profile Report (CSV); Earnings and Deductions YTD (CSV).",
        ),
        PayrollProvider(
            "paychex_flex",
            "Paychex Flex",
            "Reports → Employee Census (CSV); Payroll Journal YTD (CSV).",
        ),
        PayrollProvider(
            "quickbooks_payroll",
            "QuickBooks Payroll",
            "Reports → Employee Details (export to CSV); Payroll Summary by Employee, This Year (CSV).",
        ),
        PayrollProvider(
            "rippling",
            "Rippling",
            "Reports → Custom report with employee, compensation and YTD fields → Download CSV.",
        ),
        PayrollProvider(
            "paylocity",
            "Paylocity",
            "Reports → Employee Census and YTD Earnings reports → Export CSV.",
        ),
        PayrollProvider(
            "paycom", "Paycom", "Report Center → Employee Census and Payroll Register YTD → CSV."
        ),
        PayrollProvider(
            "square_payroll",
            "Square Payroll",
            "Team → Export team members; Payroll → Reports → Payroll summary (CSV).",
        ),
        PayrollProvider(
            "onpay", "OnPay", "Reports → Employee list and Payroll register (year to date) → CSV."
        ),
        PayrollProvider(
            "justworks", "Justworks", "Reports → Employee census and Payroll summary (YTD) → CSV."
        ),
        PayrollProvider(
            "other",
            "Another provider or spreadsheet",
            "Export employees with pay rates (and year-to-date totals if you have them) as CSV, or fill in the FlowForge template.",
        ),
    )
}

TEMPLATE_COLUMNS = [
    "Employee ID",
    "First name",
    "Last name",
    "Email",
    "Hire date",
    "Termination date",
    "Status",
    "Worker type",
    "Pay type",
    "Pay rate",
    "Pay frequency",
    "Work state",
    "Filing status",
    "Additional withholding",
    "YTD gross pay",
    "YTD federal income tax",
    "YTD social security",
    "YTD medicare",
    "YTD state income tax",
    "YTD other deductions",
    "YTD net pay",
]

# Normalised column name -> field. Names are lower-cased with non-letters removed.
_ALIASES: dict[str, tuple[str, ...]] = {
    "external_id": (
        "employeeid",
        "employeenumber",
        "empid",
        "employeeno",
        "filenumber",
        "associateid",
        "employeecode",
        "id",
        "uuid",
        "workerid",
        "personnumber",
        "positionid",
        "employee",
    ),
    "first_name": ("firstname", "legalfirstname", "givenname", "preferredfirstname", "first"),
    "last_name": ("lastname", "legallastname", "familyname", "surname", "last"),
    "full_name": ("employeename", "name", "fullname", "teammember", "employeefullname"),
    "email": ("email", "workemail", "personalemail", "emailaddress", "workemailaddress"),
    "hire_date": (
        "hiredate",
        "startdate",
        "dateofhire",
        "originalhiredate",
        "rehiredate",
        "employmentstartdate",
    ),
    "termination_date": ("terminationdate", "termdate", "dateofterm", "enddate", "separationdate"),
    "status": ("status", "employmentstatus", "positionstatus", "employeestatus"),
    "worker_type": (
        "workertype",
        "employeetype",
        "type",
        "workercategory",
        "employmenttype",
        "classification",
    ),
    "pay_type": (
        "paytype",
        "ratetype",
        "paymentunit",
        "compensationtype",
        "payclass",
        "paybasis",
        "flsastatus",
    ),
    "pay_rate": (
        "payrate",
        "rate",
        "regularpayrateamount",
        "hourlyrate",
        "annualsalary",
        "salary",
        "compensation",
        "rateamount",
        "baserate",
        "regularrate",
        "payrateamount",
        "annualpay",
    ),
    "pay_frequency": ("payfrequency", "payschedule", "payperiod", "paycycle"),
    "state": (
        "workstate",
        "state",
        "residencestate",
        "stateprovince",
        "worklocationstate",
        "taxstate",
    ),
    "filing_status": (
        "federalfilingstatus",
        "filingstatus",
        "fedfilingstatus",
        "fitfilingstatus",
        "wfilingstatus",
    ),
    "additional_withholding": (
        "additionalwithholding",
        "federaladditionalwithholding",
        "extrawithholding",
        "additionalfederalwithholding",
        "fitadditionalamount",
    ),
    "ytd_gross": (
        "ytdgrosspay",
        "ytdgross",
        "grosspayytd",
        "grossytd",
        "grosswagesytd",
        "totalgrossytd",
        "ytdgrosswages",
    ),
    "ytd_federal": (
        "ytdfederalincometax",
        "federalincometaxytd",
        "fitytd",
        "ytdfit",
        "federalwithholdingytd",
        "ytdfederalwithholding",
    ),
    "ytd_social_security": (
        "ytdsocialsecurity",
        "socialsecurityytd",
        "ytdoasdi",
        "oasdiytd",
        "ssytd",
        "ytdsocialsecuritytax",
        "socialsecuritytaxytd",
    ),
    "ytd_medicare": ("ytdmedicare", "medicareytd", "ytdmedicaretax", "medicaretaxytd"),
    "ytd_state": (
        "ytdstateincometax",
        "stateincometaxytd",
        "sitytd",
        "ytdsit",
        "ytdstatewithholding",
        "statewithholdingytd",
    ),
    "ytd_other": (
        "ytdotherdeductions",
        "ytddeductions",
        "deductionsytd",
        "totaldeductionsytd",
        "otherdeductionsytd",
    ),
    "ytd_net": ("ytdnetpay", "netpayytd", "ytdnet", "netytd", "totalnetytd"),
}
_COLUMN_TO_FIELD = {alias: name for name, aliases in _ALIASES.items() for alias in aliases}
YTD_FIELDS = {
    "ytd_gross": "gross_pay",
    "ytd_federal": "federal_income_tax",
    "ytd_social_security": "social_security_tax",
    "ytd_medicare": "medicare_tax",
    "ytd_state": "state_income_tax",
    "ytd_other": "other_deductions",
    "ytd_net": "net_pay",
}
_FREQUENCY = {
    "weekly": "weekly",
    "everyweek": "weekly",
    "biweekly": "biweekly",
    "everyotherweek": "biweekly",
    "every2weeks": "biweekly",
    "semimonthly": "semimonthly",
    "twiceamonth": "semimonthly",
    "monthly": "monthly",
    "everymonth": "monthly",
}


@dataclass(slots=True)
class EmployeeRow:
    row: int
    external_id: str
    first_name: str
    last_name: str
    email: str | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    status: str = "active"
    worker_type: str = "employee"
    pay_type: str | None = None  # hourly | salary
    pay_rate: Decimal | None = None  # hourly rate or annual salary
    pay_frequency: str = "biweekly"
    state: str | None = None
    filing_status: str | None = None
    additional_withholding: Decimal = Decimal("0")
    ytd: dict[str, Decimal] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def public(self) -> dict[str, Any]:
        return {
            "row": self.row,
            "external_id": self.external_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "termination_date": self.termination_date.isoformat()
            if self.termination_date
            else None,
            "status": self.status,
            "worker_type": self.worker_type,
            "pay_type": self.pay_type,
            "pay_rate": str(self.pay_rate) if self.pay_rate is not None else None,
            "pay_frequency": self.pay_frequency,
            "state": self.state,
            "filing_status": self.filing_status,
            "additional_withholding": str(self.additional_withholding),
            "ytd": {k: str(v) for k, v in self.ytd.items()},
            "warnings": self.warnings,
        }


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _money(text: str) -> Decimal | None:
    raw = text.strip()
    if not raw:
        return None
    negative = raw.startswith("(") or raw.startswith("-")
    cleaned = re.sub(r"[^0-9.]", "", raw)
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"'{raw[:20]}' is not an amount") from exc
    return -value if negative else value


def _date(text: str) -> date | None:
    raw = text.strip()
    if not raw:
        return None
    from .statements import parse_date

    try:
        return parse_date(raw)
    except ValueError as exc:
        raise ValueError(f"'{raw[:20]}' is not a date") from exc


def _pay(
    unit: str | None, rate: Decimal | None, frequency: str
) -> tuple[str | None, Decimal | None]:
    """(hourly|salary, hourly rate or annual salary) from a rate and its unit."""
    if rate is None:
        return None, None
    u = _norm(unit or "")
    periods = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}[frequency]
    if u in ("hour", "hourly", "perhour", "h", "hr", "nonexempt"):
        return "hourly", rate
    if u in ("week", "weekly", "perweek"):
        return "salary", rate * 52
    if u in ("month", "monthly", "permonth"):
        return "salary", rate * 12
    if u in ("paycheck", "perpaycheck", "payperiod"):
        return "salary", rate * periods
    if u in (
        "year",
        "yearly",
        "annual",
        "annually",
        "salary",
        "salaried",
        "peryear",
        "s",
        "exempt",
    ):
        return "salary", rate
    # No unit: small numbers are hourly rates, large ones annual salaries.
    return ("hourly", rate) if rate < 500 else ("salary", rate)


_STATES = dict(
    zip(
        "alabama alaska arizona arkansas california colorado connecticut delaware districtofcolumbia florida "
        "georgia hawaii idaho illinois indiana iowa kansas kentucky louisiana maine maryland massachusetts "
        "michigan minnesota mississippi missouri montana nebraska nevada newhampshire newjersey newmexico "
        "newyork northcarolina northdakota ohio oklahoma oregon pennsylvania rhodeisland southcarolina "
        "southdakota tennessee texas utah vermont virginia washington westvirginia wisconsin wyoming".split(),
        "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
        "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split(),
        strict=True,
    )
)


def state_code(text: str) -> str | None:
    raw = text.strip()
    if not raw:
        return None
    if len(raw) == 2 and raw.isalpha():
        return raw.upper()
    return _STATES.get(_norm(raw).replace("0", ""))


def parse_employee_file(text: str) -> tuple[list[EmployeeRow], list[str], dict[str, str]]:
    rows = list(csv.reader(io.StringIO(text)))
    header_index = next(
        (
            i
            for i, r in enumerate(rows[:15])
            if sum(1 for c in r if _norm(c) in _COLUMN_TO_FIELD) >= 2
        ),
        None,
    )
    if header_index is None:
        raise ValueError(
            "Could not find employee columns. The file needs a header row with at "
            "least names and an employee id, pay rate or hire date. Use the template if unsure."
        )
    header = rows[header_index]
    mapping: dict[str, int] = {}
    used: dict[str, str] = {}
    for i, column in enumerate(header):
        name = _COLUMN_TO_FIELD.get(_norm(column))
        if name and name not in mapping:
            mapping[name] = i
            used[column] = name
    if "first_name" not in mapping and "full_name" not in mapping:
        raise ValueError("The file needs first and last name columns (or one name column)")
    employees: list[EmployeeRow] = []
    errors: list[str] = []
    seen: set[str] = set()
    for number, raw in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if not any(c.strip() for c in raw):
            continue

        def get(name: str, r: list[str] = raw) -> str:
            i = mapping.get(name)
            return r[i].strip() if i is not None and i < len(r) else ""

        # Report total / summary rows ("Total", "Grand total", "Report summary").
        lead = next((c.strip().lower() for c in raw if c.strip()), "")
        if re.match(r"^(grand\s+)?(total|totals|summary|report summary)\b", lead):
            continue
        try:
            first, last = get("first_name"), get("last_name")
            if not first and get("full_name"):
                full = get("full_name")
                if "," in full:
                    last, _, first = (s.strip() for s in full.partition(","))
                else:
                    first, _, last = full.partition(" ")
            if not first and not last:
                if any(k in get("full_name").lower() for k in ("total", "summary")):
                    continue
                raise ValueError("no name")
            if (first + last).lower().startswith("total"):
                continue  # report total rows
            frequency = _FREQUENCY.get(_norm(get("pay_frequency")), "biweekly")
            pay_type, rate = _pay(get("pay_type"), _money(get("pay_rate")), frequency)
            external = (
                get("external_id") or get("email").lower() or f"{first} {last}".strip().lower()
            )
            if external in seen:
                raise ValueError(f"duplicate employee {external}")
            seen.add(external)
            status_text = get("status").lower()
            terminated = _date(get("termination_date"))
            status = (
                "terminated"
                if "term" in status_text or (terminated and terminated <= date.today())
                else "leave"
                if "leave" in status_text
                else "active"
            )
            type_text = get("worker_type").lower()
            worker_type = (
                "contractor"
                if any(w in type_text for w in ("contract", "1099"))
                else "temporary"
                if "temp" in type_text
                else "seasonal"
                if "season" in type_text
                else "intern"
                if "intern" in type_text
                else "employee"
            )
            row = EmployeeRow(
                row=number,
                external_id=external[:120],
                first_name=(first or last)[:120],
                last_name=(last or first)[:120],
                email=get("email") or None,
                hire_date=_date(get("hire_date")),
                termination_date=terminated,
                status=status,
                worker_type=worker_type,
                pay_type=pay_type,
                pay_rate=rate,
                pay_frequency=frequency,
                state=state_code(get("state")),
                filing_status=get("filing_status")[:50] or None,
                additional_withholding=_money(get("additional_withholding")) or Decimal("0"),
            )
            for source, target in YTD_FIELDS.items():
                value = _money(get(source))
                if value is not None:
                    row.ytd[target] = value
            if row.hire_date is None:
                row.warnings.append("No hire date; today's date will be used")
            if row.pay_rate is None:
                row.warnings.append("No pay rate; add it before running payroll")
            employees.append(row)
        except ValueError as exc:
            errors.append(f"Row {number}: {exc}")
    if not employees and not errors:
        raise ValueError("The file has no employees")
    return employees, errors, used


# ------------------------------------------------------------------ Gusto
def gusto_configured() -> bool:
    return bool(settings.gusto_client_id and settings.gusto_client_secret)


def _gusto_host() -> str:
    return GUSTO_HOSTS.get(settings.gusto_env, GUSTO_HOSTS["demo"])


def gusto_redirect_uri() -> str:
    return settings.public_url.rstrip("/") + "/connections/payroll/callback"


async def _gusto_get(token: str, path: str, **params: Any) -> Any:
    return await request(
        "GET",
        _gusto_host() + path,
        "Gusto",
        params=params or None,
        headers={"Authorization": f"Bearer {token}", "X-Gusto-API-Version": GUSTO_VERSION},
    )


def _gusto_pay(job: dict[str, Any], frequency: str) -> tuple[str | None, Decimal | None]:
    comps = sorted(
        job.get("compensations") or [], key=lambda c: c.get("effective_date") or "", reverse=True
    )
    current = comps[0] if comps else job
    rate = _money(str(current.get("rate") or "")) if current.get("rate") is not None else None
    return _pay(current.get("payment_unit"), rate, frequency)


async def gusto_rows(token: str, company_id: str, tax_year: int) -> list[EmployeeRow]:
    employees: list[dict[str, Any]] = []
    for page in range(1, 51):
        batch = await _gusto_get(
            token,
            f"/v1/companies/{company_id}/employees",
            include="all_compensations",
            page=page,
            per=100,
        )
        if not batch:
            break
        employees.extend(batch)
        if len(batch) < 100:
            break
    ytd: dict[str, dict[str, Decimal]] = {}
    start, end = date(tax_year, 1, 1), min(date.today(), date(tax_year, 12, 31))
    payrolls = await _gusto_get(
        token,
        f"/v1/companies/{company_id}/payrolls",
        processing_statuses="processed",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
    for summary in payrolls or []:
        pid = summary.get("payroll_uuid") or summary.get("uuid")
        if not pid:
            continue
        detail = await _gusto_get(token, f"/v1/companies/{company_id}/payrolls/{pid}")
        for comp in detail.get("employee_compensations", []):
            totals = ytd.setdefault(comp["employee_uuid"], {})

            def add(key: str, value: Any, t: dict[str, Decimal] = totals) -> None:
                t[key] = t.get(key, Decimal("0")) + Decimal(str(value or 0))

            add("gross_pay", comp.get("gross_pay"))
            add("net_pay", comp.get("net_pay"))
            for tax in comp.get("taxes", []):
                if tax.get("employer"):
                    continue
                name = str(tax.get("name", "")).lower()
                key = (
                    "federal_income_tax"
                    if "federal income" in name
                    else "social_security_tax"
                    if "social security" in name
                    else "medicare_tax"
                    if "medicare" in name
                    else "state_income_tax"
                    if "income" in name or "withholding" in name
                    else "other_deductions"
                )
                add(key, tax.get("amount"))
            for deduction in comp.get("deductions", []) + comp.get("benefits", []):
                add(
                    "other_deductions",
                    deduction.get("amount") or deduction.get("employee_deduction"),
                )
    rows: list[EmployeeRow] = []
    for number, e in enumerate(employees, start=1):
        jobs = e.get("jobs") or []
        primary = next((j for j in jobs if j.get("primary")), jobs[0] if jobs else {})
        frequency = _FREQUENCY.get(_norm(str(e.get("pay_schedule_frequency") or "")), "biweekly")
        pay_type, rate = _gusto_pay(primary, frequency)
        hire = e.get("start_date") or primary.get("hire_date")
        terminated = bool(e.get("terminated"))
        row = EmployeeRow(
            row=number,
            external_id=str(e["uuid"]),
            first_name=str(e.get("first_name") or "")[:120],
            last_name=str(e.get("last_name") or "")[:120],
            email=e.get("email") or e.get("work_email"),
            hire_date=date.fromisoformat(hire[:10]) if hire else None,
            status="terminated" if terminated else "active",
            pay_type=pay_type,
            pay_rate=rate,
            pay_frequency=frequency,
            state=((primary.get("location") or {}).get("state") or None),
        )
        row.ytd = ytd.get(str(e["uuid"]), {})
        rows.append(row)
    return rows


# ------------------------------------------------------------------ import
class PayrollImporter:
    def __init__(self, db: AsyncSession, p: Principal):
        self.db, self.p = db, p

    async def run(
        self, migration: PayrollMigration, rows: list[EmployeeRow], errors: list[str]
    ) -> PayrollMigration:
        currency = "USD"
        if await self.db.scalar(select(Currency.code).where(Currency.code == currency)) is None:
            raise ValueError("Add the currency USD in Accounting settings before importing payroll")
        created = updated = rates = ytd_rows = 0
        tax_year = migration.tax_year or date.today().year
        for row in rows:
            link = await self.db.scalar(
                select(PayrollExternalWorker).where(
                    PayrollExternalWorker.tenant_id == self.p.tenant_id,
                    PayrollExternalWorker.provider == migration.provider,
                    PayrollExternalWorker.external_id == row.external_id,
                )
            )
            worker = None
            if link is not None:
                worker = await self.db.scalar(
                    select(WorkerProfile).where(
                        WorkerProfile.id == link.worker_id,
                        WorkerProfile.tenant_id == self.p.tenant_id,
                    )
                )
            hire = row.hire_date or date.today()
            if worker is None:
                worker = await self._create_worker(row, hire, currency)
                self.db.add(
                    PayrollExternalWorker(
                        tenant_id=self.p.tenant_id,
                        provider=migration.provider,
                        external_id=row.external_id,
                        worker_id=worker.id,
                        email=row.email,
                    )
                )
                created += 1
            else:
                worker.employment_status = row.status
                worker.termination_date = row.termination_date
                worker.pay_frequency = row.pay_frequency
                updated += 1
            if row.pay_rate is not None and row.pay_type and row.pay_rate > 0:
                rates += await self._rate(worker, row, hire, currency)
            if row.filing_status:
                await self._tax_profile(worker, row, hire)
            if row.ytd:
                ytd_rows += await self._ytd(worker, row, tax_year, migration.id)
        migration.summary = {
            "employees_created": created,
            "employees_updated": updated,
            "pay_rates_set": rates,
            "ytd_balances": ytd_rows,
            "rows_skipped": len(errors),
            "tax_year": tax_year,
        }
        migration.errors = errors[:200]
        migration.status = "completed" if rows else "failed"
        migration.completed_at = datetime.now(UTC)
        await record_change(
            self.db,
            self.p.tenant_id,
            self.p.user_id,
            "imported",
            "payroll_migration",
            str(migration.id),
            migration.summary,
        )
        await self.db.commit()
        return migration

    async def _create_worker(self, row: EmployeeRow, hire: date, currency: str) -> WorkerProfile:
        name = f"{row.first_name} {row.last_name}".strip()
        party = Party(
            tenant_id=self.p.tenant_id,
            party_number=await next_number(self.db, self.p.tenant_id, "party"),
            kind="person",
            display_name=name,
            normalized_name=" ".join(name.lower().split()),
            status="active",
        )
        self.db.add(party)
        await self.db.flush()
        self.db.add(
            Person(
                tenant_id=self.p.tenant_id,
                party_id=party.id,
                given_name=row.first_name,
                family_name=row.last_name,
            )
        )
        self.db.add(
            PartyRoleAssignment(
                tenant_id=self.p.tenant_id, party_id=party.id, role="worker", effective_from=hire
            )
        )
        if row.email:
            self.db.add(
                ContactMethod(
                    tenant_id=self.p.tenant_id,
                    party_id=party.id,
                    contact_type="email",
                    value=row.email[:320],
                    normalized_value=row.email.strip().lower()[:320],
                    is_primary=True,
                )
            )
        worker = WorkerProfile(
            tenant_id=self.p.tenant_id,
            party_id=party.id,
            worker_number=await next_number(self.db, self.p.tenant_id, "worker"),
            worker_type=row.worker_type,
            employment_status=row.status,
            hire_date=hire,
            termination_date=row.termination_date,
            default_currency=currency,
            pay_frequency=row.pay_frequency,
        )
        self.db.add(worker)
        await self.db.flush()
        return worker

    async def _rate(
        self, worker: WorkerProfile, row: EmployeeRow, hire: date, currency: str
    ) -> int:
        assert row.pay_type and row.pay_rate is not None
        current = await self.db.scalar(
            select(CompensationRate)
            .where(
                CompensationRate.tenant_id == self.p.tenant_id,
                CompensationRate.worker_id == worker.id,
                CompensationRate.effective_to.is_(None),
            )
            .order_by(CompensationRate.effective_from.desc())
        )
        amount = row.pay_rate.quantize(Decimal("0.000001"))
        if (
            current is not None
            and current.compensation_type == row.pay_type
            and current.amount == amount
        ):
            return 0
        start = hire
        if current is not None:
            start = max(date.today(), current.effective_from + timedelta(days=1))
            current.effective_to = start - timedelta(days=1)
        self.db.add(
            CompensationRate(
                tenant_id=self.p.tenant_id,
                worker_id=worker.id,
                compensation_type=row.pay_type,
                amount=amount,
                currency_code=currency,
                effective_from=start,
                approved_by=self.p.user_id,
            )
        )
        return 1

    async def _tax_profile(self, worker: WorkerProfile, row: EmployeeRow, hire: date) -> None:
        existing = await self.db.scalar(
            select(WorkerTaxProfile).where(
                WorkerTaxProfile.tenant_id == self.p.tenant_id,
                WorkerTaxProfile.worker_id == worker.id,
                WorkerTaxProfile.effective_to.is_(None),
            )
        )
        if existing is not None:
            existing.filing_status = row.filing_status or existing.filing_status
            existing.additional_withholding = row.additional_withholding
            existing.residence_region = row.state or existing.residence_region
            return
        self.db.add(
            WorkerTaxProfile(
                tenant_id=self.p.tenant_id,
                worker_id=worker.id,
                residence_country="US",
                residence_region=row.state,
                filing_status=row.filing_status or "single",
                additional_withholding=row.additional_withholding,
                effective_from=hire,
            )
        )

    async def _ytd(
        self, worker: WorkerProfile, row: EmployeeRow, tax_year: int, migration_id: UUID
    ) -> int:
        balance = await self.db.scalar(
            select(PayrollYtdBalance).where(
                PayrollYtdBalance.tenant_id == self.p.tenant_id,
                PayrollYtdBalance.worker_id == worker.id,
                PayrollYtdBalance.tax_year == tax_year,
            )
        )
        if balance is None:
            balance = PayrollYtdBalance(
                tenant_id=self.p.tenant_id, worker_id=worker.id, tax_year=tax_year
            )
            self.db.add(balance)
        for key, value in row.ytd.items():
            setattr(balance, key, value.quantize(Decimal("0.01")))
        balance.migration_id = migration_id
        return 1


def _migration_public(m: PayrollMigration) -> dict[str, Any]:
    return {
        "id": str(m.id),
        "provider": m.provider,
        "provider_name": PROVIDERS.get(m.provider, PROVIDERS["other"]).name,
        "method": m.method,
        "status": m.status,
        "company_name": m.company_name,
        "filename": m.filename,
        "tax_year": m.tax_year,
        "summary": m.summary or {},
        "errors": m.errors or [],
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "completed_at": m.completed_at.isoformat() if m.completed_at else None,
    }


async def _read(file: UploadFile) -> str:
    data = await file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise ValueError("The file is too large (5 MB at most)")
    name = (file.filename or "").lower()
    if not name.endswith((".csv", ".txt")):
        raise ValueError("Upload the export as a CSV file (in Excel: File → Save As → CSV)")
    return data.decode("utf-8-sig", errors="replace")


# ------------------------------------------------------------------ routes
class GustoComplete(BaseModel):
    code: str = Field(min_length=1, max_length=500)
    state: str = Field(min_length=8, max_length=80)


class GustoImport(BaseModel):
    tax_year: int | None = Field(default=None, ge=2000, le=2100)


@router.get("/providers")
async def payroll_providers(db: D, p: P) -> dict[str, Any]:
    return {
        "providers": [
            {
                "code": x.code,
                "name": x.name,
                "export_steps": x.export_steps,
                "direct_connection": x.api and gusto_configured(),
            }
            for x in PROVIDERS.values()
        ],
        "template_columns": TEMPLATE_COLUMNS,
        "gusto_configured": gusto_configured(),
    }


@router.get("/imports")
async def payroll_imports(db: D, p: P) -> list[dict[str, Any]]:
    rows = await db.scalars(
        select(PayrollMigration)
        .where(PayrollMigration.tenant_id == p.tenant_id)
        .order_by(PayrollMigration.created_at.desc())
        .limit(50)
    )
    return [_migration_public(m) for m in rows]


@router.get("/ytd")
async def payroll_ytd(db: D, p: P, tax_year: int | None = None) -> list[dict[str, Any]]:
    year = tax_year or date.today().year
    rows = (
        await db.execute(
            select(PayrollYtdBalance, Party.display_name, WorkerProfile.worker_number)
            .join(WorkerProfile, WorkerProfile.id == PayrollYtdBalance.worker_id)
            .join(Party, Party.id == WorkerProfile.party_id)
            .where(PayrollYtdBalance.tenant_id == p.tenant_id, PayrollYtdBalance.tax_year == year)
            .order_by(Party.display_name)
        )
    ).all()
    return [
        {
            "worker_id": str(b.worker_id),
            "worker": name,
            "worker_number": number,
            "tax_year": b.tax_year,
            **{k: str(getattr(b, k)) for k in YTD_FIELDS.values()},
        }
        for b, name, number in rows
    ]


@router.post("/preview")
async def preview_payroll_file(
    db: D,
    p: P,
    file: Annotated[UploadFile, File()],
    provider: Annotated[str, Form(max_length=40)] = "other",
) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError("Unknown payroll provider")
    employees, errors, used = parse_employee_file(await _read(file))
    return {
        "employees": [e.public() for e in employees[:500]],
        "count": len(employees),
        "errors": errors[:200],
        "columns_recognised": used,
    }


@router.post("/file", status_code=201)
async def import_payroll_file(
    db: D,
    p: P,
    file: Annotated[UploadFile, File()],
    provider: Annotated[str, Form(max_length=40)] = "other",
    tax_year: Annotated[int | None, Form(ge=2000, le=2100)] = None,
) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError("Unknown payroll provider")
    text = await _read(file)
    employees, errors, _ = parse_employee_file(text)
    migration = PayrollMigration(
        tenant_id=p.tenant_id,
        provider=provider,
        method="file",
        status="running",
        filename=(file.filename or "")[:255],
        tax_year=tax_year or date.today().year,
        started_by=p.user_id,
        summary={},
        errors=[],
    )
    db.add(migration)
    await db.flush()
    await store_file(
        db,
        p,
        section="payroll",
        filename=file.filename or "payroll-import.csv",
        data=text.encode(),
        record_type="payroll_migration",
        record_id=str(migration.id),
        note=f"Payroll import from {PROVIDERS[provider].name}",
    )
    return _migration_public(await PayrollImporter(db, p).run(migration, employees, errors))


@router.post("/gusto/start")
async def start_gusto_connection(db: D, p: P) -> dict[str, Any]:
    if not gusto_configured():
        raise ValueError(
            "The direct Gusto connection is not set up on this server yet "
            "(FLOWFORGE_GUSTO_CLIENT_ID and FLOWFORGE_GUSTO_CLIENT_SECRET). Import a Gusto export file instead."
        )
    state = secrets.token_urlsafe(24)
    migration = PayrollMigration(
        tenant_id=p.tenant_id,
        provider="gusto",
        method="api",
        status="authorizing",
        oauth_state=state,
        started_by=p.user_id,
        summary={},
        errors=[],
    )
    db.add(migration)
    await db.commit()
    url = (
        _gusto_host()
        + "/oauth/authorize?"
        + urlencode(
            {
                "client_id": settings.gusto_client_id,
                "redirect_uri": gusto_redirect_uri(),
                "response_type": "code",
                "state": state,
            }
        )
    )
    return {"authorize_url": url, "migration_id": str(migration.id)}


@router.post("/gusto/complete")
async def complete_gusto_connection(db: D, p: P, body: GustoComplete) -> dict[str, Any]:
    migration = await db.scalar(
        select(PayrollMigration).where(
            PayrollMigration.tenant_id == p.tenant_id,
            PayrollMigration.oauth_state == body.state,
            PayrollMigration.status == "authorizing",
        )
    )
    if migration is None:
        raise ValueError("This Gusto sign-in has expired or was already used; start again")
    if migration.created_at and datetime.now(UTC) - migration.created_at > timedelta(minutes=30):
        migration.status = "failed"
        await db.commit()
        raise ValueError("This Gusto sign-in has expired; start again")
    token = await request(
        "POST",
        _gusto_host() + "/oauth/token",
        "Gusto",
        json={
            "client_id": settings.gusto_client_id,
            "client_secret": settings.gusto_client_secret,
            "code": body.code,
            "grant_type": "authorization_code",
            "redirect_uri": gusto_redirect_uri(),
        },
    )
    access = token["access_token"]
    info = await _gusto_get(access, "/v1/token_info")
    company_id = ((info or {}).get("resource") or {}).get("uuid")
    if not company_id:
        raise ProviderError("Gusto did not say which company was authorised")
    company = await _gusto_get(access, f"/v1/companies/{company_id}")
    migration.company_name = str(
        company.get("trade_name") or company.get("name") or "Gusto company"
    )[:200]
    migration.encrypted_tokens = crypto.encrypt_json(
        {
            "access_token": access,
            "refresh_token": token.get("refresh_token"),
            "company_id": company_id,
        },
        f"{p.tenant_id}:payroll:{migration.id}",
    )
    migration.oauth_state = None
    migration.status = "connected"
    await db.commit()
    return _migration_public(migration)


@router.post("/imports/{migration_id}/sync")
async def sync_gusto(db: D, p: P, migration_id: UUID, body: GustoImport) -> dict[str, Any]:
    migration = await db.scalar(
        select(PayrollMigration).where(
            PayrollMigration.id == migration_id, PayrollMigration.tenant_id == p.tenant_id
        )
    )
    if migration is None:
        raise LookupError("Payroll connection not found")
    if migration.method != "api" or not migration.encrypted_tokens:
        raise ValueError("Only a connected Gusto account can be synced")
    tokens = crypto.decrypt_json(
        migration.encrypted_tokens, f"{p.tenant_id}:payroll:{migration.id}"
    )
    migration.tax_year = body.tax_year or date.today().year
    try:
        rows = await gusto_rows(
            str(tokens["access_token"]), str(tokens["company_id"]), migration.tax_year
        )
    except ProviderError as exc:
        if "(401)" in str(exc) and tokens.get("refresh_token"):
            refreshed = await request(
                "POST",
                _gusto_host() + "/oauth/token",
                "Gusto",
                json={
                    "client_id": settings.gusto_client_id,
                    "client_secret": settings.gusto_client_secret,
                    "refresh_token": tokens["refresh_token"],
                    "grant_type": "refresh_token",
                },
            )
            tokens.update(
                access_token=refreshed["access_token"],
                refresh_token=refreshed.get("refresh_token", tokens["refresh_token"]),
            )
            migration.encrypted_tokens = crypto.encrypt_json(
                tokens, f"{p.tenant_id}:payroll:{migration.id}"
            )
            rows = await gusto_rows(
                str(tokens["access_token"]), str(tokens["company_id"]), migration.tax_year
            )
        else:
            raise
    migration.status = "running"
    result = await PayrollImporter(db, p).run(migration, rows, [])
    result.status = "completed"
    await db.commit()
    return _migration_public(result)
