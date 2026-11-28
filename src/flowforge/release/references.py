"""Which table an id field points to, so the UI can offer a drop-down of real records.

Sources, in order:
1. Foreign keys in the models: a column named ``vendor_id`` that references
   ``ap_vendors.id`` maps ``vendor_id`` to ``ap_vendors`` (the most common target wins
   when the same name references different tables).
2. Naming: ``lead_id`` -> a tenant table called ``leads`` or ending in ``_leads``
   (preferring the operation's own workspace tables, then the shortest name).
3. Path parameters named ``id``: the collection segment before it
   (``/crm/leads/{id}/convert`` -> leads).

Only tenant tables (with ``tenant_id``) are offered: those are what the record browser
(/api/v1/business/<table>) can list for the signed-in tenant.
"""

from collections import Counter
from collections.abc import Iterable
from functools import lru_cache

from flowforge.db.base import Base

# Ids that are not FlowForge records (provider references, free-form sources).
_SKIP = {"tenant_id", "idempotency_key", "external_id", "source_id", "target_id"}
_SKIP_PREFIXES = ("provider_", "external_", "institution_", "source_record_")
# Short names used in paths and bodies.
_ALIASES = {"po": "purchase_orders"}


@lru_cache(maxsize=1)
def _tenant_tables() -> frozenset[str]:
    return frozenset(
        table.name for table in Base.metadata.tables.values() if "tenant_id" in table.c
    )


@lru_cache(maxsize=1)
def _foreign_keys() -> dict[str, Counter[str]]:
    tenant = _tenant_tables()
    seen: dict[str, Counter[str]] = {}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            for fk in column.foreign_keys:
                target = fk.column.table.name
                if target in tenant and fk.column.name == "id":
                    seen.setdefault(column.name, Counter())[target] += 1
    return seen


def _plurals(stem: str) -> list[str]:
    forms = [stem, f"{stem}s", f"{stem}es"]
    if stem.endswith("y"):
        forms.append(f"{stem[:-1]}ies")
    return forms


def _by_name(stem: str, preferred: Iterable[str]) -> str | None:
    tenant = _tenant_tables()
    forms = _plurals(stem)
    matches = [t for t in tenant if any(t == f or t.endswith(f"_{f}") for f in forms)]
    if not matches:
        return None
    local = [t for t in matches if t in set(preferred)]
    pool = local or matches
    return sorted(pool, key=lambda t: (len(t), t))[0]


def reference_for(name: str, preferred: Iterable[str] = ()) -> str | None:
    """Table an id field named ``name`` refers to, if it can be told."""
    if name in _SKIP or name.startswith(_SKIP_PREFIXES) or not name.endswith("_id"):
        return None
    preferred = set(preferred)
    counts = _foreign_keys().get(name)
    if counts:
        local = [t for t, _ in counts.most_common() if t in preferred]
        if local:
            return local[0]
        # Several targets: take a clear majority; a generic name (parent_id) whose
        # targets are spread out falls through to naming, which finds none.
        top, top_count = counts.most_common(1)[0]
        if len(counts) == 1 or top_count * 2 > sum(counts.values()):
            return top
    words = name[: -len("_id")].split("_")
    # cash_account_id -> cash_account, then account; tax_payable_account_id -> ... account.
    for start in range(len(words)):
        stem = "_".join(words[start:])
        if stem in _ALIASES:
            return _ALIASES[stem]
        found = _by_name(stem, preferred)
        if found:
            return found
    return None


def reference_for_path(path: str, name: str, preferred: Iterable[str] = ()) -> str | None:
    """Path parameter: by its name, or for a bare ``{id}`` by the segment before it."""
    found = reference_for(name, preferred)
    if found or name != "id":
        return found
    parts = [p for p in path.split("/") if p]
    marker = "{" + name + "}"
    if marker not in parts:
        return None
    index = parts.index(marker)
    if index == 0 or parts[index - 1].startswith("{"):
        return None
    segment = parts[index - 1].replace("-", "_")
    for stem in (segment, segment.rstrip("s"), segment[:-2] if segment.endswith("es") else ""):
        if stem:
            found = _by_name(stem, preferred)
            if found:
                return found
    return None
