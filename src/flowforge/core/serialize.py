"""Turn ORM instances into plain JSON-ready values for endpoint responses."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm.base import NO_VALUE


def orm_dict(obj: Any) -> Any:
    """Column values of an ORM instance (or a list of them).

    Only already-loaded attributes are read, so this never triggers a lazy load
    (which would fail in async code). Values the database filled in but the
    session has not loaded are omitted; refresh first if they are needed.
    """
    if obj is None or isinstance(obj, (str, int, float, bool, dict)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [orm_dict(item) for item in obj]
    state = inspect(obj, raiseerr=False)
    if state is None or not hasattr(state, "mapper"):
        return obj
    out: dict[str, Any] = {}
    for attr in state.mapper.column_attrs:
        value = state.attrs[attr.key].loaded_value
        if value is not NO_VALUE:
            out[attr.key] = value
    return out
