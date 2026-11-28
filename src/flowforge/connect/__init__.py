"""Connections release: uploads in every section, bank feeds, payroll migration and
shipping carrier tracking."""

from fastapi import APIRouter

from . import banking, files, payroll, shipping, status

router = APIRouter()
for module in (files, banking, payroll, shipping, status):
    router.include_router(module.router)

MODULES = {
    "flowforge.connect.files",
    "flowforge.connect.banking",
    "flowforge.connect.payroll",
    "flowforge.connect.shipping",
    "flowforge.connect.status",
}
