from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TenantRecordMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft", index=True)
    code: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class IdentityUsers(TenantRecordMixin, Base):
    __tablename__ = "identity_users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_users_tenant_code"),
        Index("ix_identity_users_tenant_status", "tenant_id", "status"),
    )

class IdentityInvitations(TenantRecordMixin, Base):
    __tablename__ = "identity_invitations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_invitations_tenant_code"),
        Index("ix_identity_invitations_tenant_status", "tenant_id", "status"),
    )

class IdentityRoles(TenantRecordMixin, Base):
    __tablename__ = "identity_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_roles_tenant_code"),
        Index("ix_identity_roles_tenant_status", "tenant_id", "status"),
    )

class IdentityPermissions(TenantRecordMixin, Base):
    __tablename__ = "identity_permissions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_permissions_tenant_code"),
        Index("ix_identity_permissions_tenant_status", "tenant_id", "status"),
    )

class IdentitySessions(TenantRecordMixin, Base):
    __tablename__ = "identity_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_sessions_tenant_code"),
        Index("ix_identity_sessions_tenant_status", "tenant_id", "status"),
    )

class IdentityMfaEnrollments(TenantRecordMixin, Base):
    __tablename__ = "identity_mfa_enrollments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_mfa_enrollments_tenant_code"),
        Index("ix_identity_mfa_enrollments_tenant_status", "tenant_id", "status"),
    )

class IdentityDevices(TenantRecordMixin, Base):
    __tablename__ = "identity_devices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_devices_tenant_code"),
        Index("ix_identity_devices_tenant_status", "tenant_id", "status"),
    )

class IdentityAccessReviews(TenantRecordMixin, Base):
    __tablename__ = "identity_access_reviews"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_access_reviews_tenant_code"),
        Index("ix_identity_access_reviews_tenant_status", "tenant_id", "status"),
    )

class IdentityServiceAccounts(TenantRecordMixin, Base):
    __tablename__ = "identity_service_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_service_accounts_tenant_code"),
        Index("ix_identity_service_accounts_tenant_status", "tenant_id", "status"),
    )

class IdentitySsoConnections(TenantRecordMixin, Base):
    __tablename__ = "identity_sso_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_identity_sso_connections_tenant_code"),
        Index("ix_identity_sso_connections_tenant_status", "tenant_id", "status"),
    )

class TenantsTenants(TenantRecordMixin, Base):
    __tablename__ = "tenants_tenants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_tenants_tenant_code"),
        Index("ix_tenants_tenants_tenant_status", "tenant_id", "status"),
    )

class TenantsLegalEntities(TenantRecordMixin, Base):
    __tablename__ = "tenants_legal_entities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_legal_entities_tenant_code"),
        Index("ix_tenants_legal_entities_tenant_status", "tenant_id", "status"),
    )

class TenantsBusinessUnits(TenantRecordMixin, Base):
    __tablename__ = "tenants_business_units"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_business_units_tenant_code"),
        Index("ix_tenants_business_units_tenant_status", "tenant_id", "status"),
    )

class TenantsModuleEntitlements(TenantRecordMixin, Base):
    __tablename__ = "tenants_module_entitlements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_module_entitlements_tenant_code"),
        Index("ix_tenants_module_entitlements_tenant_status", "tenant_id", "status"),
    )

class TenantsBranding(TenantRecordMixin, Base):
    __tablename__ = "tenants_branding"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_branding_tenant_code"),
        Index("ix_tenants_branding_tenant_status", "tenant_id", "status"),
    )

class TenantsDomains(TenantRecordMixin, Base):
    __tablename__ = "tenants_domains"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_domains_tenant_code"),
        Index("ix_tenants_domains_tenant_status", "tenant_id", "status"),
    )

class TenantsSandboxes(TenantRecordMixin, Base):
    __tablename__ = "tenants_sandboxes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_sandboxes_tenant_code"),
        Index("ix_tenants_sandboxes_tenant_status", "tenant_id", "status"),
    )

class TenantsDataExports(TenantRecordMixin, Base):
    __tablename__ = "tenants_data_exports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_data_exports_tenant_code"),
        Index("ix_tenants_data_exports_tenant_status", "tenant_id", "status"),
    )

class TenantsRestoreRequests(TenantRecordMixin, Base):
    __tablename__ = "tenants_restore_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_restore_requests_tenant_code"),
        Index("ix_tenants_restore_requests_tenant_status", "tenant_id", "status"),
    )

class TenantsUsageMeters(TenantRecordMixin, Base):
    __tablename__ = "tenants_usage_meters"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tenants_usage_meters_tenant_code"),
        Index("ix_tenants_usage_meters_tenant_status", "tenant_id", "status"),
    )

class AuditAuditEvents(TenantRecordMixin, Base):
    __tablename__ = "audit_audit_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_audit_events_tenant_code"),
        Index("ix_audit_audit_events_tenant_status", "tenant_id", "status"),
    )

class AuditRecordVersions(TenantRecordMixin, Base):
    __tablename__ = "audit_record_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_record_versions_tenant_code"),
        Index("ix_audit_record_versions_tenant_status", "tenant_id", "status"),
    )

class AuditLegalHolds(TenantRecordMixin, Base):
    __tablename__ = "audit_legal_holds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_legal_holds_tenant_code"),
        Index("ix_audit_legal_holds_tenant_status", "tenant_id", "status"),
    )

class AuditRetentionPolicies(TenantRecordMixin, Base):
    __tablename__ = "audit_retention_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_retention_policies_tenant_code"),
        Index("ix_audit_retention_policies_tenant_status", "tenant_id", "status"),
    )

class AuditEvidencePackages(TenantRecordMixin, Base):
    __tablename__ = "audit_evidence_packages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_evidence_packages_tenant_code"),
        Index("ix_audit_evidence_packages_tenant_status", "tenant_id", "status"),
    )

class AuditControlTests(TenantRecordMixin, Base):
    __tablename__ = "audit_control_tests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_control_tests_tenant_code"),
        Index("ix_audit_control_tests_tenant_status", "tenant_id", "status"),
    )

class AuditFindings(TenantRecordMixin, Base):
    __tablename__ = "audit_findings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_findings_tenant_code"),
        Index("ix_audit_findings_tenant_status", "tenant_id", "status"),
    )

class AuditRemediations(TenantRecordMixin, Base):
    __tablename__ = "audit_remediations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_remediations_tenant_code"),
        Index("ix_audit_remediations_tenant_status", "tenant_id", "status"),
    )

class AuditRiskRegisters(TenantRecordMixin, Base):
    __tablename__ = "audit_risk_registers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_risk_registers_tenant_code"),
        Index("ix_audit_risk_registers_tenant_status", "tenant_id", "status"),
    )

class AuditElectronicSignatures(TenantRecordMixin, Base):
    __tablename__ = "audit_electronic_signatures"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_audit_electronic_signatures_tenant_code"),
        Index("ix_audit_electronic_signatures_tenant_status", "tenant_id", "status"),
    )

class WorkflowWorkflowDefinitions(TenantRecordMixin, Base):
    __tablename__ = "workflow_workflow_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_workflow_definitions_tenant_code"),
        Index("ix_workflow_workflow_definitions_tenant_status", "tenant_id", "status"),
    )

class WorkflowWorkflowRuns(TenantRecordMixin, Base):
    __tablename__ = "workflow_workflow_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_workflow_runs_tenant_code"),
        Index("ix_workflow_workflow_runs_tenant_status", "tenant_id", "status"),
    )

class WorkflowTasks(TenantRecordMixin, Base):
    __tablename__ = "workflow_tasks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_tasks_tenant_code"),
        Index("ix_workflow_tasks_tenant_status", "tenant_id", "status"),
    )

class WorkflowApprovals(TenantRecordMixin, Base):
    __tablename__ = "workflow_approvals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_approvals_tenant_code"),
        Index("ix_workflow_approvals_tenant_status", "tenant_id", "status"),
    )

class WorkflowDelegations(TenantRecordMixin, Base):
    __tablename__ = "workflow_delegations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_delegations_tenant_code"),
        Index("ix_workflow_delegations_tenant_status", "tenant_id", "status"),
    )

class WorkflowEscalations(TenantRecordMixin, Base):
    __tablename__ = "workflow_escalations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_escalations_tenant_code"),
        Index("ix_workflow_escalations_tenant_status", "tenant_id", "status"),
    )

class WorkflowComments(TenantRecordMixin, Base):
    __tablename__ = "workflow_comments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_comments_tenant_code"),
        Index("ix_workflow_comments_tenant_status", "tenant_id", "status"),
    )

class WorkflowAttachments(TenantRecordMixin, Base):
    __tablename__ = "workflow_attachments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_attachments_tenant_code"),
        Index("ix_workflow_attachments_tenant_status", "tenant_id", "status"),
    )

class DocumentsDocuments(TenantRecordMixin, Base):
    __tablename__ = "documents_documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_documents_tenant_code"),
        Index("ix_documents_documents_tenant_status", "tenant_id", "status"),
    )

class DocumentsDocumentVersions(TenantRecordMixin, Base):
    __tablename__ = "documents_document_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_document_versions_tenant_code"),
        Index("ix_documents_document_versions_tenant_status", "tenant_id", "status"),
    )

class DocumentsClassifications(TenantRecordMixin, Base):
    __tablename__ = "documents_classifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_classifications_tenant_code"),
        Index("ix_documents_classifications_tenant_status", "tenant_id", "status"),
    )

class DocumentsExtractions(TenantRecordMixin, Base):
    __tablename__ = "documents_extractions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_extractions_tenant_code"),
        Index("ix_documents_extractions_tenant_status", "tenant_id", "status"),
    )

class DocumentsAnnotations(TenantRecordMixin, Base):
    __tablename__ = "documents_annotations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_annotations_tenant_code"),
        Index("ix_documents_annotations_tenant_status", "tenant_id", "status"),
    )

class DocumentsControlledDocuments(TenantRecordMixin, Base):
    __tablename__ = "documents_controlled_documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_controlled_documents_tenant_code"),
        Index("ix_documents_controlled_documents_tenant_status", "tenant_id", "status"),
    )

class DocumentsTrainingAssignments(TenantRecordMixin, Base):
    __tablename__ = "documents_training_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_training_assignments_tenant_code"),
        Index("ix_documents_training_assignments_tenant_status", "tenant_id", "status"),
    )

class DocumentsContracts(TenantRecordMixin, Base):
    __tablename__ = "documents_contracts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_contracts_tenant_code"),
        Index("ix_documents_contracts_tenant_status", "tenant_id", "status"),
    )

class DocumentsSignatureRequests(TenantRecordMixin, Base):
    __tablename__ = "documents_signature_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_signature_requests_tenant_code"),
        Index("ix_documents_signature_requests_tenant_status", "tenant_id", "status"),
    )

class DocumentsLegalHolds(TenantRecordMixin, Base):
    __tablename__ = "documents_legal_holds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_documents_legal_holds_tenant_code"),
        Index("ix_documents_legal_holds_tenant_status", "tenant_id", "status"),
    )

class ApVendors(TenantRecordMixin, Base):
    __tablename__ = "ap_vendors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_vendors_tenant_code"),
        Index("ix_ap_vendors_tenant_status", "tenant_id", "status"),
    )

class ApVendorAccounts(TenantRecordMixin, Base):
    __tablename__ = "ap_vendor_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_vendor_accounts_tenant_code"),
        Index("ix_ap_vendor_accounts_tenant_status", "tenant_id", "status"),
    )

class ApRequisitions(TenantRecordMixin, Base):
    __tablename__ = "ap_requisitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_requisitions_tenant_code"),
        Index("ix_ap_requisitions_tenant_status", "tenant_id", "status"),
    )

class ApRfqs(TenantRecordMixin, Base):
    __tablename__ = "ap_rfqs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_rfqs_tenant_code"),
        Index("ix_ap_rfqs_tenant_status", "tenant_id", "status"),
    )

class ApPurchaseOrders(TenantRecordMixin, Base):
    __tablename__ = "ap_purchase_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_purchase_orders_tenant_code"),
        Index("ix_ap_purchase_orders_tenant_status", "tenant_id", "status"),
    )

class ApReceipts(TenantRecordMixin, Base):
    __tablename__ = "ap_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_receipts_tenant_code"),
        Index("ix_ap_receipts_tenant_status", "tenant_id", "status"),
    )

class ApSupplierReturns(TenantRecordMixin, Base):
    __tablename__ = "ap_supplier_returns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_supplier_returns_tenant_code"),
        Index("ix_ap_supplier_returns_tenant_status", "tenant_id", "status"),
    )

class ApBills(TenantRecordMixin, Base):
    __tablename__ = "ap_bills"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_bills_tenant_code"),
        Index("ix_ap_bills_tenant_status", "tenant_id", "status"),
    )

class ApCreditMemos(TenantRecordMixin, Base):
    __tablename__ = "ap_credit_memos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_credit_memos_tenant_code"),
        Index("ix_ap_credit_memos_tenant_status", "tenant_id", "status"),
    )

class ApMatchExceptions(TenantRecordMixin, Base):
    __tablename__ = "ap_match_exceptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_match_exceptions_tenant_code"),
        Index("ix_ap_match_exceptions_tenant_status", "tenant_id", "status"),
    )

class ApPaymentProposals(TenantRecordMixin, Base):
    __tablename__ = "ap_payment_proposals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_payment_proposals_tenant_code"),
        Index("ix_ap_payment_proposals_tenant_status", "tenant_id", "status"),
    )

class ApPayments(TenantRecordMixin, Base):
    __tablename__ = "ap_payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_payments_tenant_code"),
        Index("ix_ap_payments_tenant_status", "tenant_id", "status"),
    )

class ApRemittances(TenantRecordMixin, Base):
    __tablename__ = "ap_remittances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_remittances_tenant_code"),
        Index("ix_ap_remittances_tenant_status", "tenant_id", "status"),
    )

class ApVendorStatements(TenantRecordMixin, Base):
    __tablename__ = "ap_vendor_statements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ap_vendor_statements_tenant_code"),
        Index("ix_ap_vendor_statements_tenant_status", "tenant_id", "status"),
    )

class ArCustomers(TenantRecordMixin, Base):
    __tablename__ = "ar_customers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_customers_tenant_code"),
        Index("ix_ar_customers_tenant_status", "tenant_id", "status"),
    )

class ArCreditProfiles(TenantRecordMixin, Base):
    __tablename__ = "ar_credit_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_credit_profiles_tenant_code"),
        Index("ix_ar_credit_profiles_tenant_status", "tenant_id", "status"),
    )

class ArQuotes(TenantRecordMixin, Base):
    __tablename__ = "ar_quotes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_quotes_tenant_code"),
        Index("ix_ar_quotes_tenant_status", "tenant_id", "status"),
    )

class ArSalesOrders(TenantRecordMixin, Base):
    __tablename__ = "ar_sales_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_sales_orders_tenant_code"),
        Index("ix_ar_sales_orders_tenant_status", "tenant_id", "status"),
    )

class ArInvoices(TenantRecordMixin, Base):
    __tablename__ = "ar_invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_invoices_tenant_code"),
        Index("ix_ar_invoices_tenant_status", "tenant_id", "status"),
    )

class ArCreditMemos(TenantRecordMixin, Base):
    __tablename__ = "ar_credit_memos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_credit_memos_tenant_code"),
        Index("ix_ar_credit_memos_tenant_status", "tenant_id", "status"),
    )

class ArReceipts(TenantRecordMixin, Base):
    __tablename__ = "ar_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_receipts_tenant_code"),
        Index("ix_ar_receipts_tenant_status", "tenant_id", "status"),
    )

class ArCashApplications(TenantRecordMixin, Base):
    __tablename__ = "ar_cash_applications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_cash_applications_tenant_code"),
        Index("ix_ar_cash_applications_tenant_status", "tenant_id", "status"),
    )

class ArStatements(TenantRecordMixin, Base):
    __tablename__ = "ar_statements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_statements_tenant_code"),
        Index("ix_ar_statements_tenant_status", "tenant_id", "status"),
    )

class ArCollectionCases(TenantRecordMixin, Base):
    __tablename__ = "ar_collection_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_collection_cases_tenant_code"),
        Index("ix_ar_collection_cases_tenant_status", "tenant_id", "status"),
    )

class ArDisputes(TenantRecordMixin, Base):
    __tablename__ = "ar_disputes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_disputes_tenant_code"),
        Index("ix_ar_disputes_tenant_status", "tenant_id", "status"),
    )

class ArWriteOffs(TenantRecordMixin, Base):
    __tablename__ = "ar_write_offs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_write_offs_tenant_code"),
        Index("ix_ar_write_offs_tenant_status", "tenant_id", "status"),
    )

class ArRefunds(TenantRecordMixin, Base):
    __tablename__ = "ar_refunds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ar_refunds_tenant_code"),
        Index("ix_ar_refunds_tenant_status", "tenant_id", "status"),
    )

class LedgerAccounts(TenantRecordMixin, Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_accounts_tenant_code"),
        Index("ix_ledger_accounts_tenant_status", "tenant_id", "status"),
    )

class LedgerJournals(TenantRecordMixin, Base):
    __tablename__ = "ledger_journals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_journals_tenant_code"),
        Index("ix_ledger_journals_tenant_status", "tenant_id", "status"),
    )

class LedgerJournalLines(TenantRecordMixin, Base):
    __tablename__ = "ledger_journal_lines"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_journal_lines_tenant_code"),
        Index("ix_ledger_journal_lines_tenant_status", "tenant_id", "status"),
    )

class LedgerRecurringJournals(TenantRecordMixin, Base):
    __tablename__ = "ledger_recurring_journals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_recurring_journals_tenant_code"),
        Index("ix_ledger_recurring_journals_tenant_status", "tenant_id", "status"),
    )

class LedgerAllocations(TenantRecordMixin, Base):
    __tablename__ = "ledger_allocations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_allocations_tenant_code"),
        Index("ix_ledger_allocations_tenant_status", "tenant_id", "status"),
    )

class LedgerAccruals(TenantRecordMixin, Base):
    __tablename__ = "ledger_accruals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_accruals_tenant_code"),
        Index("ix_ledger_accruals_tenant_status", "tenant_id", "status"),
    )

class LedgerPrepaids(TenantRecordMixin, Base):
    __tablename__ = "ledger_prepaids"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_prepaids_tenant_code"),
        Index("ix_ledger_prepaids_tenant_status", "tenant_id", "status"),
    )

class LedgerDeferredRevenue(TenantRecordMixin, Base):
    __tablename__ = "ledger_deferred_revenue"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_deferred_revenue_tenant_code"),
        Index("ix_ledger_deferred_revenue_tenant_status", "tenant_id", "status"),
    )

class LedgerPeriods(TenantRecordMixin, Base):
    __tablename__ = "ledger_periods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_periods_tenant_code"),
        Index("ix_ledger_periods_tenant_status", "tenant_id", "status"),
    )

class LedgerCloseTasks(TenantRecordMixin, Base):
    __tablename__ = "ledger_close_tasks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_close_tasks_tenant_code"),
        Index("ix_ledger_close_tasks_tenant_status", "tenant_id", "status"),
    )

class LedgerTrialBalances(TenantRecordMixin, Base):
    __tablename__ = "ledger_trial_balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_trial_balances_tenant_code"),
        Index("ix_ledger_trial_balances_tenant_status", "tenant_id", "status"),
    )

class LedgerConsolidations(TenantRecordMixin, Base):
    __tablename__ = "ledger_consolidations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_consolidations_tenant_code"),
        Index("ix_ledger_consolidations_tenant_status", "tenant_id", "status"),
    )

class LedgerEliminations(TenantRecordMixin, Base):
    __tablename__ = "ledger_eliminations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_eliminations_tenant_code"),
        Index("ix_ledger_eliminations_tenant_status", "tenant_id", "status"),
    )

class LedgerBudgets(TenantRecordMixin, Base):
    __tablename__ = "ledger_budgets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_budgets_tenant_code"),
        Index("ix_ledger_budgets_tenant_status", "tenant_id", "status"),
    )

class LedgerScenarios(TenantRecordMixin, Base):
    __tablename__ = "ledger_scenarios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_scenarios_tenant_code"),
        Index("ix_ledger_scenarios_tenant_status", "tenant_id", "status"),
    )

class BankingBankAccounts(TenantRecordMixin, Base):
    __tablename__ = "banking_bank_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_bank_accounts_tenant_code"),
        Index("ix_banking_bank_accounts_tenant_status", "tenant_id", "status"),
    )

class BankingBankConnections(TenantRecordMixin, Base):
    __tablename__ = "banking_bank_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_bank_connections_tenant_code"),
        Index("ix_banking_bank_connections_tenant_status", "tenant_id", "status"),
    )

class BankingBankTransactions(TenantRecordMixin, Base):
    __tablename__ = "banking_bank_transactions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_bank_transactions_tenant_code"),
        Index("ix_banking_bank_transactions_tenant_status", "tenant_id", "status"),
    )

class BankingReconciliationRules(TenantRecordMixin, Base):
    __tablename__ = "banking_reconciliation_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_reconciliation_rules_tenant_code"),
        Index("ix_banking_reconciliation_rules_tenant_status", "tenant_id", "status"),
    )

class BankingReconciliations(TenantRecordMixin, Base):
    __tablename__ = "banking_reconciliations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_reconciliations_tenant_code"),
        Index("ix_banking_reconciliations_tenant_status", "tenant_id", "status"),
    )

class BankingPaymentBatches(TenantRecordMixin, Base):
    __tablename__ = "banking_payment_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_payment_batches_tenant_code"),
        Index("ix_banking_payment_batches_tenant_status", "tenant_id", "status"),
    )

class BankingTransfers(TenantRecordMixin, Base):
    __tablename__ = "banking_transfers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_transfers_tenant_code"),
        Index("ix_banking_transfers_tenant_status", "tenant_id", "status"),
    )

class BankingAchFiles(TenantRecordMixin, Base):
    __tablename__ = "banking_ach_files"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_ach_files_tenant_code"),
        Index("ix_banking_ach_files_tenant_status", "tenant_id", "status"),
    )

class BankingWires(TenantRecordMixin, Base):
    __tablename__ = "banking_wires"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_wires_tenant_code"),
        Index("ix_banking_wires_tenant_status", "tenant_id", "status"),
    )

class BankingPositivePayFiles(TenantRecordMixin, Base):
    __tablename__ = "banking_positive_pay_files"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_positive_pay_files_tenant_code"),
        Index("ix_banking_positive_pay_files_tenant_status", "tenant_id", "status"),
    )

class BankingCashForecasts(TenantRecordMixin, Base):
    __tablename__ = "banking_cash_forecasts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_cash_forecasts_tenant_code"),
        Index("ix_banking_cash_forecasts_tenant_status", "tenant_id", "status"),
    )

class BankingDebtFacilities(TenantRecordMixin, Base):
    __tablename__ = "banking_debt_facilities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_banking_debt_facilities_tenant_code"),
        Index("ix_banking_debt_facilities_tenant_status", "tenant_id", "status"),
    )

class InventoryItems(TenantRecordMixin, Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_items_tenant_code"),
        Index("ix_inventory_items_tenant_status", "tenant_id", "status"),
    )

class InventoryVariants(TenantRecordMixin, Base):
    __tablename__ = "inventory_variants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_variants_tenant_code"),
        Index("ix_inventory_variants_tenant_status", "tenant_id", "status"),
    )

class InventoryUnitsOfMeasure(TenantRecordMixin, Base):
    __tablename__ = "inventory_units_of_measure"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_units_of_measure_tenant_code"),
        Index("ix_inventory_units_of_measure_tenant_status", "tenant_id", "status"),
    )

class InventoryWarehouses(TenantRecordMixin, Base):
    __tablename__ = "inventory_warehouses"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_warehouses_tenant_code"),
        Index("ix_inventory_warehouses_tenant_status", "tenant_id", "status"),
    )

class InventoryBins(TenantRecordMixin, Base):
    __tablename__ = "inventory_bins"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_bins_tenant_code"),
        Index("ix_inventory_bins_tenant_status", "tenant_id", "status"),
    )

class InventoryLots(TenantRecordMixin, Base):
    __tablename__ = "inventory_lots"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_lots_tenant_code"),
        Index("ix_inventory_lots_tenant_status", "tenant_id", "status"),
    )

class InventorySerials(TenantRecordMixin, Base):
    __tablename__ = "inventory_serials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_serials_tenant_code"),
        Index("ix_inventory_serials_tenant_status", "tenant_id", "status"),
    )

class InventoryReservations(TenantRecordMixin, Base):
    __tablename__ = "inventory_reservations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_reservations_tenant_code"),
        Index("ix_inventory_reservations_tenant_status", "tenant_id", "status"),
    )

class InventoryInventoryEvents(TenantRecordMixin, Base):
    __tablename__ = "inventory_inventory_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_inventory_events_tenant_code"),
        Index("ix_inventory_inventory_events_tenant_status", "tenant_id", "status"),
    )

class InventoryBalances(TenantRecordMixin, Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_balances_tenant_code"),
        Index("ix_inventory_balances_tenant_status", "tenant_id", "status"),
    )

class InventoryTransfers(TenantRecordMixin, Base):
    __tablename__ = "inventory_transfers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_transfers_tenant_code"),
        Index("ix_inventory_transfers_tenant_status", "tenant_id", "status"),
    )

class InventoryAdjustments(TenantRecordMixin, Base):
    __tablename__ = "inventory_adjustments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_adjustments_tenant_code"),
        Index("ix_inventory_adjustments_tenant_status", "tenant_id", "status"),
    )

class InventoryCycleCounts(TenantRecordMixin, Base):
    __tablename__ = "inventory_cycle_counts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_cycle_counts_tenant_code"),
        Index("ix_inventory_cycle_counts_tenant_status", "tenant_id", "status"),
    )

class InventoryReplenishmentProposals(TenantRecordMixin, Base):
    __tablename__ = "inventory_replenishment_proposals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_replenishment_proposals_tenant_code"),
        Index("ix_inventory_replenishment_proposals_tenant_status", "tenant_id", "status"),
    )

class InventoryValuationRuns(TenantRecordMixin, Base):
    __tablename__ = "inventory_valuation_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_valuation_runs_tenant_code"),
        Index("ix_inventory_valuation_runs_tenant_status", "tenant_id", "status"),
    )

class InventoryLandedCosts(TenantRecordMixin, Base):
    __tablename__ = "inventory_landed_costs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inventory_landed_costs_tenant_code"),
        Index("ix_inventory_landed_costs_tenant_status", "tenant_id", "status"),
    )

class ManufacturingBillsOfMaterial(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_bills_of_material"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_bills_of_material_tenant_code"),
        Index("ix_manufacturing_bills_of_material_tenant_status", "tenant_id", "status"),
    )

class ManufacturingWorkOrders(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_work_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_work_orders_tenant_code"),
        Index("ix_manufacturing_work_orders_tenant_status", "tenant_id", "status"),
    )

class ManufacturingMaterialRequirements(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_material_requirements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_material_requirements_tenant_code"),
        Index("ix_manufacturing_material_requirements_tenant_status", "tenant_id", "status"),
    )

class ManufacturingProductionSchedules(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_production_schedules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_production_schedules_tenant_code"),
        Index("ix_manufacturing_production_schedules_tenant_status", "tenant_id", "status"),
    )

class ManufacturingShopFloorEvents(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_shop_floor_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_shop_floor_events_tenant_code"),
        Index("ix_manufacturing_shop_floor_events_tenant_status", "tenant_id", "status"),
    )

class ManufacturingJobCosts(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_job_costs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_job_costs_tenant_code"),
        Index("ix_manufacturing_job_costs_tenant_status", "tenant_id", "status"),
    )

class ManufacturingYieldRecords(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_yield_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_yield_records_tenant_code"),
        Index("ix_manufacturing_yield_records_tenant_status", "tenant_id", "status"),
    )

class ManufacturingScrapRecords(TenantRecordMixin, Base):
    __tablename__ = "manufacturing_scrap_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_manufacturing_scrap_records_tenant_code"),
        Index("ix_manufacturing_scrap_records_tenant_status", "tenant_id", "status"),
    )

class ShippingCarrierConnections(TenantRecordMixin, Base):
    __tablename__ = "shipping_carrier_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_carrier_connections_tenant_code"),
        Index("ix_shipping_carrier_connections_tenant_status", "tenant_id", "status"),
    )

class ShippingRateQuotes(TenantRecordMixin, Base):
    __tablename__ = "shipping_rate_quotes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_rate_quotes_tenant_code"),
        Index("ix_shipping_rate_quotes_tenant_status", "tenant_id", "status"),
    )

class ShippingShipments(TenantRecordMixin, Base):
    __tablename__ = "shipping_shipments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_shipments_tenant_code"),
        Index("ix_shipping_shipments_tenant_status", "tenant_id", "status"),
    )

class ShippingPackages(TenantRecordMixin, Base):
    __tablename__ = "shipping_packages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_packages_tenant_code"),
        Index("ix_shipping_packages_tenant_status", "tenant_id", "status"),
    )

class ShippingLabels(TenantRecordMixin, Base):
    __tablename__ = "shipping_labels"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_labels_tenant_code"),
        Index("ix_shipping_labels_tenant_status", "tenant_id", "status"),
    )

class ShippingPickups(TenantRecordMixin, Base):
    __tablename__ = "shipping_pickups"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_pickups_tenant_code"),
        Index("ix_shipping_pickups_tenant_status", "tenant_id", "status"),
    )

class ShippingTrackingEvents(TenantRecordMixin, Base):
    __tablename__ = "shipping_tracking_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_tracking_events_tenant_code"),
        Index("ix_shipping_tracking_events_tenant_status", "tenant_id", "status"),
    )

class ShippingDeliveryExceptions(TenantRecordMixin, Base):
    __tablename__ = "shipping_delivery_exceptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_delivery_exceptions_tenant_code"),
        Index("ix_shipping_delivery_exceptions_tenant_status", "tenant_id", "status"),
    )

class ShippingClaims(TenantRecordMixin, Base):
    __tablename__ = "shipping_claims"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_claims_tenant_code"),
        Index("ix_shipping_claims_tenant_status", "tenant_id", "status"),
    )

class ShippingReturns(TenantRecordMixin, Base):
    __tablename__ = "shipping_returns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_returns_tenant_code"),
        Index("ix_shipping_returns_tenant_status", "tenant_id", "status"),
    )

class ShippingCostReconciliations(TenantRecordMixin, Base):
    __tablename__ = "shipping_cost_reconciliations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_shipping_cost_reconciliations_tenant_code"),
        Index("ix_shipping_cost_reconciliations_tenant_status", "tenant_id", "status"),
    )

class WorkforceWorkers(TenantRecordMixin, Base):
    __tablename__ = "workforce_workers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_workers_tenant_code"),
        Index("ix_workforce_workers_tenant_status", "tenant_id", "status"),
    )

class WorkforcePositions(TenantRecordMixin, Base):
    __tablename__ = "workforce_positions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_positions_tenant_code"),
        Index("ix_workforce_positions_tenant_status", "tenant_id", "status"),
    )

class WorkforceJobs(TenantRecordMixin, Base):
    __tablename__ = "workforce_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_jobs_tenant_code"),
        Index("ix_workforce_jobs_tenant_status", "tenant_id", "status"),
    )

class WorkforceDepartments(TenantRecordMixin, Base):
    __tablename__ = "workforce_departments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_departments_tenant_code"),
        Index("ix_workforce_departments_tenant_status", "tenant_id", "status"),
    )

class WorkforceCompensationChanges(TenantRecordMixin, Base):
    __tablename__ = "workforce_compensation_changes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_compensation_changes_tenant_code"),
        Index("ix_workforce_compensation_changes_tenant_status", "tenant_id", "status"),
    )

class WorkforceOnboardingCases(TenantRecordMixin, Base):
    __tablename__ = "workforce_onboarding_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_onboarding_cases_tenant_code"),
        Index("ix_workforce_onboarding_cases_tenant_status", "tenant_id", "status"),
    )

class WorkforceOffboardingCases(TenantRecordMixin, Base):
    __tablename__ = "workforce_offboarding_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_offboarding_cases_tenant_code"),
        Index("ix_workforce_offboarding_cases_tenant_status", "tenant_id", "status"),
    )

class WorkforceTimecards(TenantRecordMixin, Base):
    __tablename__ = "workforce_timecards"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_timecards_tenant_code"),
        Index("ix_workforce_timecards_tenant_status", "tenant_id", "status"),
    )

class WorkforceShifts(TenantRecordMixin, Base):
    __tablename__ = "workforce_shifts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_shifts_tenant_code"),
        Index("ix_workforce_shifts_tenant_status", "tenant_id", "status"),
    )

class WorkforcePtoBalances(TenantRecordMixin, Base):
    __tablename__ = "workforce_pto_balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_pto_balances_tenant_code"),
        Index("ix_workforce_pto_balances_tenant_status", "tenant_id", "status"),
    )

class WorkforceLeaveRequests(TenantRecordMixin, Base):
    __tablename__ = "workforce_leave_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_leave_requests_tenant_code"),
        Index("ix_workforce_leave_requests_tenant_status", "tenant_id", "status"),
    )

class WorkforceCertifications(TenantRecordMixin, Base):
    __tablename__ = "workforce_certifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_certifications_tenant_code"),
        Index("ix_workforce_certifications_tenant_status", "tenant_id", "status"),
    )

class WorkforceTrainingRecords(TenantRecordMixin, Base):
    __tablename__ = "workforce_training_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_training_records_tenant_code"),
        Index("ix_workforce_training_records_tenant_status", "tenant_id", "status"),
    )

class WorkforcePerformanceReviews(TenantRecordMixin, Base):
    __tablename__ = "workforce_performance_reviews"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_performance_reviews_tenant_code"),
        Index("ix_workforce_performance_reviews_tenant_status", "tenant_id", "status"),
    )

class WorkforceGoals(TenantRecordMixin, Base):
    __tablename__ = "workforce_goals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_goals_tenant_code"),
        Index("ix_workforce_goals_tenant_status", "tenant_id", "status"),
    )

class PayrollPayrollGroups(TenantRecordMixin, Base):
    __tablename__ = "payroll_payroll_groups"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_payroll_groups_tenant_code"),
        Index("ix_payroll_payroll_groups_tenant_status", "tenant_id", "status"),
    )

class PayrollPaySchedules(TenantRecordMixin, Base):
    __tablename__ = "payroll_pay_schedules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_pay_schedules_tenant_code"),
        Index("ix_payroll_pay_schedules_tenant_status", "tenant_id", "status"),
    )

class PayrollPayrollPeriods(TenantRecordMixin, Base):
    __tablename__ = "payroll_payroll_periods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_payroll_periods_tenant_code"),
        Index("ix_payroll_payroll_periods_tenant_status", "tenant_id", "status"),
    )

class PayrollPayrollRuns(TenantRecordMixin, Base):
    __tablename__ = "payroll_payroll_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_payroll_runs_tenant_code"),
        Index("ix_payroll_payroll_runs_tenant_status", "tenant_id", "status"),
    )

class PayrollPayrollWorkers(TenantRecordMixin, Base):
    __tablename__ = "payroll_payroll_workers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_payroll_workers_tenant_code"),
        Index("ix_payroll_payroll_workers_tenant_status", "tenant_id", "status"),
    )

class PayrollEarnings(TenantRecordMixin, Base):
    __tablename__ = "payroll_earnings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_earnings_tenant_code"),
        Index("ix_payroll_earnings_tenant_status", "tenant_id", "status"),
    )

class PayrollDeductions(TenantRecordMixin, Base):
    __tablename__ = "payroll_deductions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_deductions_tenant_code"),
        Index("ix_payroll_deductions_tenant_status", "tenant_id", "status"),
    )

class PayrollGarnishments(TenantRecordMixin, Base):
    __tablename__ = "payroll_garnishments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_garnishments_tenant_code"),
        Index("ix_payroll_garnishments_tenant_status", "tenant_id", "status"),
    )

class PayrollTaxCalculations(TenantRecordMixin, Base):
    __tablename__ = "payroll_tax_calculations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_tax_calculations_tenant_code"),
        Index("ix_payroll_tax_calculations_tenant_status", "tenant_id", "status"),
    )

class PayrollExceptions(TenantRecordMixin, Base):
    __tablename__ = "payroll_exceptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_exceptions_tenant_code"),
        Index("ix_payroll_exceptions_tenant_status", "tenant_id", "status"),
    )

class PayrollApprovals(TenantRecordMixin, Base):
    __tablename__ = "payroll_approvals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_approvals_tenant_code"),
        Index("ix_payroll_approvals_tenant_status", "tenant_id", "status"),
    )

class PayrollProviderConnections(TenantRecordMixin, Base):
    __tablename__ = "payroll_provider_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_provider_connections_tenant_code"),
        Index("ix_payroll_provider_connections_tenant_status", "tenant_id", "status"),
    )

class PayrollSyncJobs(TenantRecordMixin, Base):
    __tablename__ = "payroll_sync_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_sync_jobs_tenant_code"),
        Index("ix_payroll_sync_jobs_tenant_status", "tenant_id", "status"),
    )

class PayrollCodeMappings(TenantRecordMixin, Base):
    __tablename__ = "payroll_code_mappings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_code_mappings_tenant_code"),
        Index("ix_payroll_code_mappings_tenant_status", "tenant_id", "status"),
    )

class PayrollParallelRuns(TenantRecordMixin, Base):
    __tablename__ = "payroll_parallel_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_parallel_runs_tenant_code"),
        Index("ix_payroll_parallel_runs_tenant_status", "tenant_id", "status"),
    )

class PayrollVarianceResults(TenantRecordMixin, Base):
    __tablename__ = "payroll_variance_results"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_variance_results_tenant_code"),
        Index("ix_payroll_variance_results_tenant_status", "tenant_id", "status"),
    )

class PayrollCutoverPlans(TenantRecordMixin, Base):
    __tablename__ = "payroll_cutover_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_cutover_plans_tenant_code"),
        Index("ix_payroll_cutover_plans_tenant_status", "tenant_id", "status"),
    )

class PayrollPayrollRegisters(TenantRecordMixin, Base):
    __tablename__ = "payroll_payroll_registers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_payroll_registers_tenant_code"),
        Index("ix_payroll_payroll_registers_tenant_status", "tenant_id", "status"),
    )

class PayrollPayrollJournals(TenantRecordMixin, Base):
    __tablename__ = "payroll_payroll_journals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_payroll_payroll_journals_tenant_code"),
        Index("ix_payroll_payroll_journals_tenant_status", "tenant_id", "status"),
    )

class BenefitsBenefitPlans(TenantRecordMixin, Base):
    __tablename__ = "benefits_benefit_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_benefit_plans_tenant_code"),
        Index("ix_benefits_benefit_plans_tenant_status", "tenant_id", "status"),
    )

class BenefitsEligibilityRules(TenantRecordMixin, Base):
    __tablename__ = "benefits_eligibility_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_eligibility_rules_tenant_code"),
        Index("ix_benefits_eligibility_rules_tenant_status", "tenant_id", "status"),
    )

class BenefitsEnrollments(TenantRecordMixin, Base):
    __tablename__ = "benefits_enrollments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_enrollments_tenant_code"),
        Index("ix_benefits_enrollments_tenant_status", "tenant_id", "status"),
    )

class BenefitsDependents(TenantRecordMixin, Base):
    __tablename__ = "benefits_dependents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_dependents_tenant_code"),
        Index("ix_benefits_dependents_tenant_status", "tenant_id", "status"),
    )

class BenefitsLifeEvents(TenantRecordMixin, Base):
    __tablename__ = "benefits_life_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_life_events_tenant_code"),
        Index("ix_benefits_life_events_tenant_status", "tenant_id", "status"),
    )

class BenefitsCobraEvents(TenantRecordMixin, Base):
    __tablename__ = "benefits_cobra_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_cobra_events_tenant_code"),
        Index("ix_benefits_cobra_events_tenant_status", "tenant_id", "status"),
    )

class BenefitsAcaMeasurements(TenantRecordMixin, Base):
    __tablename__ = "benefits_aca_measurements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_aca_measurements_tenant_code"),
        Index("ix_benefits_aca_measurements_tenant_status", "tenant_id", "status"),
    )

class BenefitsRetirementPlans(TenantRecordMixin, Base):
    __tablename__ = "benefits_retirement_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_retirement_plans_tenant_code"),
        Index("ix_benefits_retirement_plans_tenant_status", "tenant_id", "status"),
    )

class BenefitsRetirementElections(TenantRecordMixin, Base):
    __tablename__ = "benefits_retirement_elections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_retirement_elections_tenant_code"),
        Index("ix_benefits_retirement_elections_tenant_status", "tenant_id", "status"),
    )

class BenefitsContributions(TenantRecordMixin, Base):
    __tablename__ = "benefits_contributions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_contributions_tenant_code"),
        Index("ix_benefits_contributions_tenant_status", "tenant_id", "status"),
    )

class BenefitsLoans(TenantRecordMixin, Base):
    __tablename__ = "benefits_loans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_loans_tenant_code"),
        Index("ix_benefits_loans_tenant_status", "tenant_id", "status"),
    )

class BenefitsRemittances(TenantRecordMixin, Base):
    __tablename__ = "benefits_remittances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_remittances_tenant_code"),
        Index("ix_benefits_remittances_tenant_status", "tenant_id", "status"),
    )

class BenefitsReconciliations(TenantRecordMixin, Base):
    __tablename__ = "benefits_reconciliations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_benefits_reconciliations_tenant_code"),
        Index("ix_benefits_reconciliations_tenant_status", "tenant_id", "status"),
    )

class TaxJurisdictions(TenantRecordMixin, Base):
    __tablename__ = "tax_jurisdictions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_jurisdictions_tenant_code"),
        Index("ix_tax_jurisdictions_tenant_status", "tenant_id", "status"),
    )

class TaxRegistrations(TenantRecordMixin, Base):
    __tablename__ = "tax_registrations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_registrations_tenant_code"),
        Index("ix_tax_registrations_tenant_status", "tenant_id", "status"),
    )

class TaxNexusAssessments(TenantRecordMixin, Base):
    __tablename__ = "tax_nexus_assessments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_nexus_assessments_tenant_code"),
        Index("ix_tax_nexus_assessments_tenant_status", "tenant_id", "status"),
    )

class TaxObligations(TenantRecordMixin, Base):
    __tablename__ = "tax_obligations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_obligations_tenant_code"),
        Index("ix_tax_obligations_tenant_status", "tenant_id", "status"),
    )

class TaxCalculationRuns(TenantRecordMixin, Base):
    __tablename__ = "tax_calculation_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_calculation_runs_tenant_code"),
        Index("ix_tax_calculation_runs_tenant_status", "tenant_id", "status"),
    )

class TaxFilings(TenantRecordMixin, Base):
    __tablename__ = "tax_filings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_filings_tenant_code"),
        Index("ix_tax_filings_tenant_status", "tenant_id", "status"),
    )

class TaxPayments(TenantRecordMixin, Base):
    __tablename__ = "tax_payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_payments_tenant_code"),
        Index("ix_tax_payments_tenant_status", "tenant_id", "status"),
    )

class TaxAgencyNotices(TenantRecordMixin, Base):
    __tablename__ = "tax_agency_notices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_agency_notices_tenant_code"),
        Index("ix_tax_agency_notices_tenant_status", "tenant_id", "status"),
    )

class TaxNoticeCases(TenantRecordMixin, Base):
    __tablename__ = "tax_notice_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_notice_cases_tenant_code"),
        Index("ix_tax_notice_cases_tenant_status", "tenant_id", "status"),
    )

class TaxAmendments(TenantRecordMixin, Base):
    __tablename__ = "tax_amendments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_amendments_tenant_code"),
        Index("ix_tax_amendments_tenant_status", "tenant_id", "status"),
    )

class TaxReconciliations(TenantRecordMixin, Base):
    __tablename__ = "tax_reconciliations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_reconciliations_tenant_code"),
        Index("ix_tax_reconciliations_tenant_status", "tenant_id", "status"),
    )

class TaxTaxDocuments(TenantRecordMixin, Base):
    __tablename__ = "tax_tax_documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tax_tax_documents_tenant_code"),
        Index("ix_tax_tax_documents_tenant_status", "tenant_id", "status"),
    )

class QualityCapas(TenantRecordMixin, Base):
    __tablename__ = "quality_capas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_capas_tenant_code"),
        Index("ix_quality_capas_tenant_status", "tenant_id", "status"),
    )

class QualityNonconformances(TenantRecordMixin, Base):
    __tablename__ = "quality_nonconformances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_nonconformances_tenant_code"),
        Index("ix_quality_nonconformances_tenant_status", "tenant_id", "status"),
    )

class QualityComplaints(TenantRecordMixin, Base):
    __tablename__ = "quality_complaints"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_complaints_tenant_code"),
        Index("ix_quality_complaints_tenant_status", "tenant_id", "status"),
    )

class QualitySupplierQualifications(TenantRecordMixin, Base):
    __tablename__ = "quality_supplier_qualifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_supplier_qualifications_tenant_code"),
        Index("ix_quality_supplier_qualifications_tenant_status", "tenant_id", "status"),
    )

class QualityQualityAudits(TenantRecordMixin, Base):
    __tablename__ = "quality_quality_audits"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_quality_audits_tenant_code"),
        Index("ix_quality_quality_audits_tenant_status", "tenant_id", "status"),
    )

class QualityInspections(TenantRecordMixin, Base):
    __tablename__ = "quality_inspections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_inspections_tenant_code"),
        Index("ix_quality_inspections_tenant_status", "tenant_id", "status"),
    )

class QualityChangeControls(TenantRecordMixin, Base):
    __tablename__ = "quality_change_controls"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_change_controls_tenant_code"),
        Index("ix_quality_change_controls_tenant_status", "tenant_id", "status"),
    )

class QualityDeviations(TenantRecordMixin, Base):
    __tablename__ = "quality_deviations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_deviations_tenant_code"),
        Index("ix_quality_deviations_tenant_status", "tenant_id", "status"),
    )

class QualityValidationProtocols(TenantRecordMixin, Base):
    __tablename__ = "quality_validation_protocols"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_validation_protocols_tenant_code"),
        Index("ix_quality_validation_protocols_tenant_status", "tenant_id", "status"),
    )

class QualityValidationRuns(TenantRecordMixin, Base):
    __tablename__ = "quality_validation_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_validation_runs_tenant_code"),
        Index("ix_quality_validation_runs_tenant_status", "tenant_id", "status"),
    )

class QualityRiskFiles(TenantRecordMixin, Base):
    __tablename__ = "quality_risk_files"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_risk_files_tenant_code"),
        Index("ix_quality_risk_files_tenant_status", "tenant_id", "status"),
    )

class QualityFmeas(TenantRecordMixin, Base):
    __tablename__ = "quality_fmeas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_fmeas_tenant_code"),
        Index("ix_quality_fmeas_tenant_status", "tenant_id", "status"),
    )

class QualityDeviceMasterRecords(TenantRecordMixin, Base):
    __tablename__ = "quality_device_master_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_device_master_records_tenant_code"),
        Index("ix_quality_device_master_records_tenant_status", "tenant_id", "status"),
    )

class QualityDeviceHistoryRecords(TenantRecordMixin, Base):
    __tablename__ = "quality_device_history_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_device_history_records_tenant_code"),
        Index("ix_quality_device_history_records_tenant_status", "tenant_id", "status"),
    )

class QualityTraceabilityEvents(TenantRecordMixin, Base):
    __tablename__ = "quality_traceability_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_quality_traceability_events_tenant_code"),
        Index("ix_quality_traceability_events_tenant_status", "tenant_id", "status"),
    )

class ProjectsProjects(TenantRecordMixin, Base):
    __tablename__ = "projects_projects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_projects_tenant_code"),
        Index("ix_projects_projects_tenant_status", "tenant_id", "status"),
    )

class ProjectsTasks(TenantRecordMixin, Base):
    __tablename__ = "projects_tasks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_tasks_tenant_code"),
        Index("ix_projects_tasks_tenant_status", "tenant_id", "status"),
    )

class ProjectsMilestones(TenantRecordMixin, Base):
    __tablename__ = "projects_milestones"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_milestones_tenant_code"),
        Index("ix_projects_milestones_tenant_status", "tenant_id", "status"),
    )

class ProjectsBudgets(TenantRecordMixin, Base):
    __tablename__ = "projects_budgets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_budgets_tenant_code"),
        Index("ix_projects_budgets_tenant_status", "tenant_id", "status"),
    )

class ProjectsResourceAssignments(TenantRecordMixin, Base):
    __tablename__ = "projects_resource_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_resource_assignments_tenant_code"),
        Index("ix_projects_resource_assignments_tenant_status", "tenant_id", "status"),
    )

class ProjectsTimeEntries(TenantRecordMixin, Base):
    __tablename__ = "projects_time_entries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_time_entries_tenant_code"),
        Index("ix_projects_time_entries_tenant_status", "tenant_id", "status"),
    )

class ProjectsExpenses(TenantRecordMixin, Base):
    __tablename__ = "projects_expenses"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_expenses_tenant_code"),
        Index("ix_projects_expenses_tenant_status", "tenant_id", "status"),
    )

class ProjectsCostCodes(TenantRecordMixin, Base):
    __tablename__ = "projects_cost_codes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_cost_codes_tenant_code"),
        Index("ix_projects_cost_codes_tenant_status", "tenant_id", "status"),
    )

class ProjectsChangeOrders(TenantRecordMixin, Base):
    __tablename__ = "projects_change_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_change_orders_tenant_code"),
        Index("ix_projects_change_orders_tenant_status", "tenant_id", "status"),
    )

class ProjectsBillingEvents(TenantRecordMixin, Base):
    __tablename__ = "projects_billing_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_billing_events_tenant_code"),
        Index("ix_projects_billing_events_tenant_status", "tenant_id", "status"),
    )

class ProjectsProfitabilitySnapshots(TenantRecordMixin, Base):
    __tablename__ = "projects_profitability_snapshots"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_profitability_snapshots_tenant_code"),
        Index("ix_projects_profitability_snapshots_tenant_status", "tenant_id", "status"),
    )

class AssetsAssetClasses(TenantRecordMixin, Base):
    __tablename__ = "assets_asset_classes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_asset_classes_tenant_code"),
        Index("ix_assets_asset_classes_tenant_status", "tenant_id", "status"),
    )

class AssetsAssets(TenantRecordMixin, Base):
    __tablename__ = "assets_assets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_assets_tenant_code"),
        Index("ix_assets_assets_tenant_status", "tenant_id", "status"),
    )

class AssetsDepreciationBooks(TenantRecordMixin, Base):
    __tablename__ = "assets_depreciation_books"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_depreciation_books_tenant_code"),
        Index("ix_assets_depreciation_books_tenant_status", "tenant_id", "status"),
    )

class AssetsDepreciationRuns(TenantRecordMixin, Base):
    __tablename__ = "assets_depreciation_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_depreciation_runs_tenant_code"),
        Index("ix_assets_depreciation_runs_tenant_status", "tenant_id", "status"),
    )

class AssetsAssetTransfers(TenantRecordMixin, Base):
    __tablename__ = "assets_asset_transfers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_asset_transfers_tenant_code"),
        Index("ix_assets_asset_transfers_tenant_status", "tenant_id", "status"),
    )

class AssetsMaintenanceRecords(TenantRecordMixin, Base):
    __tablename__ = "assets_maintenance_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_maintenance_records_tenant_code"),
        Index("ix_assets_maintenance_records_tenant_status", "tenant_id", "status"),
    )

class AssetsImpairments(TenantRecordMixin, Base):
    __tablename__ = "assets_impairments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_impairments_tenant_code"),
        Index("ix_assets_impairments_tenant_status", "tenant_id", "status"),
    )

class AssetsDisposals(TenantRecordMixin, Base):
    __tablename__ = "assets_disposals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_disposals_tenant_code"),
        Index("ix_assets_disposals_tenant_status", "tenant_id", "status"),
    )

class AssetsLeaseRecords(TenantRecordMixin, Base):
    __tablename__ = "assets_lease_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assets_lease_records_tenant_code"),
        Index("ix_assets_lease_records_tenant_status", "tenant_id", "status"),
    )

class IntegrationsProviderDefinitions(TenantRecordMixin, Base):
    __tablename__ = "integrations_provider_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_provider_definitions_tenant_code"),
        Index("ix_integrations_provider_definitions_tenant_status", "tenant_id", "status"),
    )

class IntegrationsConnections(TenantRecordMixin, Base):
    __tablename__ = "integrations_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_connections_tenant_code"),
        Index("ix_integrations_connections_tenant_status", "tenant_id", "status"),
    )

class IntegrationsCredentials(TenantRecordMixin, Base):
    __tablename__ = "integrations_credentials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_credentials_tenant_code"),
        Index("ix_integrations_credentials_tenant_status", "tenant_id", "status"),
    )

class IntegrationsOauthAuthorizations(TenantRecordMixin, Base):
    __tablename__ = "integrations_oauth_authorizations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_oauth_authorizations_tenant_code"),
        Index("ix_integrations_oauth_authorizations_tenant_status", "tenant_id", "status"),
    )

class IntegrationsWebhookEndpoints(TenantRecordMixin, Base):
    __tablename__ = "integrations_webhook_endpoints"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_webhook_endpoints_tenant_code"),
        Index("ix_integrations_webhook_endpoints_tenant_status", "tenant_id", "status"),
    )

class IntegrationsWebhookDeliveries(TenantRecordMixin, Base):
    __tablename__ = "integrations_webhook_deliveries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_webhook_deliveries_tenant_code"),
        Index("ix_integrations_webhook_deliveries_tenant_status", "tenant_id", "status"),
    )

class IntegrationsSyncJobs(TenantRecordMixin, Base):
    __tablename__ = "integrations_sync_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_sync_jobs_tenant_code"),
        Index("ix_integrations_sync_jobs_tenant_status", "tenant_id", "status"),
    )

class IntegrationsSyncCheckpoints(TenantRecordMixin, Base):
    __tablename__ = "integrations_sync_checkpoints"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_sync_checkpoints_tenant_code"),
        Index("ix_integrations_sync_checkpoints_tenant_status", "tenant_id", "status"),
    )

class IntegrationsMappingRules(TenantRecordMixin, Base):
    __tablename__ = "integrations_mapping_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_mapping_rules_tenant_code"),
        Index("ix_integrations_mapping_rules_tenant_status", "tenant_id", "status"),
    )

class IntegrationsConflicts(TenantRecordMixin, Base):
    __tablename__ = "integrations_conflicts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_conflicts_tenant_code"),
        Index("ix_integrations_conflicts_tenant_status", "tenant_id", "status"),
    )

class IntegrationsDeadLetters(TenantRecordMixin, Base):
    __tablename__ = "integrations_dead_letters"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_dead_letters_tenant_code"),
        Index("ix_integrations_dead_letters_tenant_status", "tenant_id", "status"),
    )

class IntegrationsHealthChecks(TenantRecordMixin, Base):
    __tablename__ = "integrations_health_checks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_health_checks_tenant_code"),
        Index("ix_integrations_health_checks_tenant_status", "tenant_id", "status"),
    )

class IntegrationsActivationGates(TenantRecordMixin, Base):
    __tablename__ = "integrations_activation_gates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_integrations_activation_gates_tenant_code"),
        Index("ix_integrations_activation_gates_tenant_status", "tenant_id", "status"),
    )

class AiConversations(TenantRecordMixin, Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_conversations_tenant_code"),
        Index("ix_ai_conversations_tenant_status", "tenant_id", "status"),
    )

class AiMessages(TenantRecordMixin, Base):
    __tablename__ = "ai_messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_messages_tenant_code"),
        Index("ix_ai_messages_tenant_status", "tenant_id", "status"),
    )

class AiRetrievalQueries(TenantRecordMixin, Base):
    __tablename__ = "ai_retrieval_queries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_retrieval_queries_tenant_code"),
        Index("ix_ai_retrieval_queries_tenant_status", "tenant_id", "status"),
    )

class AiCitations(TenantRecordMixin, Base):
    __tablename__ = "ai_citations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_citations_tenant_code"),
        Index("ix_ai_citations_tenant_status", "tenant_id", "status"),
    )

class AiDocumentIngestions(TenantRecordMixin, Base):
    __tablename__ = "ai_document_ingestions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_document_ingestions_tenant_code"),
        Index("ix_ai_document_ingestions_tenant_status", "tenant_id", "status"),
    )

class AiActionProposals(TenantRecordMixin, Base):
    __tablename__ = "ai_action_proposals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_action_proposals_tenant_code"),
        Index("ix_ai_action_proposals_tenant_status", "tenant_id", "status"),
    )

class AiApprovals(TenantRecordMixin, Base):
    __tablename__ = "ai_approvals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_approvals_tenant_code"),
        Index("ix_ai_approvals_tenant_status", "tenant_id", "status"),
    )

class AiUsageRecords(TenantRecordMixin, Base):
    __tablename__ = "ai_usage_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_usage_records_tenant_code"),
        Index("ix_ai_usage_records_tenant_status", "tenant_id", "status"),
    )

class AiSafetyEvents(TenantRecordMixin, Base):
    __tablename__ = "ai_safety_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ai_safety_events_tenant_code"),
        Index("ix_ai_safety_events_tenant_status", "tenant_id", "status"),
    )

class SearchIndexes(TenantRecordMixin, Base):
    __tablename__ = "search_indexes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_search_indexes_tenant_code"),
        Index("ix_search_indexes_tenant_status", "tenant_id", "status"),
    )

class SearchSearchQueries(TenantRecordMixin, Base):
    __tablename__ = "search_search_queries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_search_search_queries_tenant_code"),
        Index("ix_search_search_queries_tenant_status", "tenant_id", "status"),
    )

class SearchSavedSearches(TenantRecordMixin, Base):
    __tablename__ = "search_saved_searches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_search_saved_searches_tenant_code"),
        Index("ix_search_saved_searches_tenant_status", "tenant_id", "status"),
    )

class SearchRecentSearches(TenantRecordMixin, Base):
    __tablename__ = "search_recent_searches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_search_recent_searches_tenant_code"),
        Index("ix_search_recent_searches_tenant_status", "tenant_id", "status"),
    )

class SearchReindexJobs(TenantRecordMixin, Base):
    __tablename__ = "search_reindex_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_search_reindex_jobs_tenant_code"),
        Index("ix_search_reindex_jobs_tenant_status", "tenant_id", "status"),
    )

class ReportingReportDefinitions(TenantRecordMixin, Base):
    __tablename__ = "reporting_report_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_report_definitions_tenant_code"),
        Index("ix_reporting_report_definitions_tenant_status", "tenant_id", "status"),
    )

class ReportingReportRuns(TenantRecordMixin, Base):
    __tablename__ = "reporting_report_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_report_runs_tenant_code"),
        Index("ix_reporting_report_runs_tenant_status", "tenant_id", "status"),
    )

class ReportingScheduledReports(TenantRecordMixin, Base):
    __tablename__ = "reporting_scheduled_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_scheduled_reports_tenant_code"),
        Index("ix_reporting_scheduled_reports_tenant_status", "tenant_id", "status"),
    )

class ReportingDashboards(TenantRecordMixin, Base):
    __tablename__ = "reporting_dashboards"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_dashboards_tenant_code"),
        Index("ix_reporting_dashboards_tenant_status", "tenant_id", "status"),
    )

class ReportingDashboardLayouts(TenantRecordMixin, Base):
    __tablename__ = "reporting_dashboard_layouts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_dashboard_layouts_tenant_code"),
        Index("ix_reporting_dashboard_layouts_tenant_status", "tenant_id", "status"),
    )

class ReportingKpiDefinitions(TenantRecordMixin, Base):
    __tablename__ = "reporting_kpi_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_kpi_definitions_tenant_code"),
        Index("ix_reporting_kpi_definitions_tenant_status", "tenant_id", "status"),
    )

class ReportingForecasts(TenantRecordMixin, Base):
    __tablename__ = "reporting_forecasts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_forecasts_tenant_code"),
        Index("ix_reporting_forecasts_tenant_status", "tenant_id", "status"),
    )

class ReportingScenarios(TenantRecordMixin, Base):
    __tablename__ = "reporting_scenarios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_scenarios_tenant_code"),
        Index("ix_reporting_scenarios_tenant_status", "tenant_id", "status"),
    )

class ReportingSnapshots(TenantRecordMixin, Base):
    __tablename__ = "reporting_snapshots"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_snapshots_tenant_code"),
        Index("ix_reporting_snapshots_tenant_status", "tenant_id", "status"),
    )

class ReportingExports(TenantRecordMixin, Base):
    __tablename__ = "reporting_exports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_reporting_exports_tenant_code"),
        Index("ix_reporting_exports_tenant_status", "tenant_id", "status"),
    )

class PortalsPortalUsers(TenantRecordMixin, Base):
    __tablename__ = "portals_portal_users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_portals_portal_users_tenant_code"),
        Index("ix_portals_portal_users_tenant_status", "tenant_id", "status"),
    )

class PortalsCustomerPortalSessions(TenantRecordMixin, Base):
    __tablename__ = "portals_customer_portal_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_portals_customer_portal_sessions_tenant_code"),
        Index("ix_portals_customer_portal_sessions_tenant_status", "tenant_id", "status"),
    )

class PortalsVendorPortalSessions(TenantRecordMixin, Base):
    __tablename__ = "portals_vendor_portal_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_portals_vendor_portal_sessions_tenant_code"),
        Index("ix_portals_vendor_portal_sessions_tenant_status", "tenant_id", "status"),
    )

class PortalsEmployeePortalSessions(TenantRecordMixin, Base):
    __tablename__ = "portals_employee_portal_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_portals_employee_portal_sessions_tenant_code"),
        Index("ix_portals_employee_portal_sessions_tenant_status", "tenant_id", "status"),
    )

class PortalsAuditorAccessGrants(TenantRecordMixin, Base):
    __tablename__ = "portals_auditor_access_grants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_portals_auditor_access_grants_tenant_code"),
        Index("ix_portals_auditor_access_grants_tenant_status", "tenant_id", "status"),
    )

class PortalsPortalBranding(TenantRecordMixin, Base):
    __tablename__ = "portals_portal_branding"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_portals_portal_branding_tenant_code"),
        Index("ix_portals_portal_branding_tenant_status", "tenant_id", "status"),
    )

class BillingProducts(TenantRecordMixin, Base):
    __tablename__ = "billing_products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_products_tenant_code"),
        Index("ix_billing_products_tenant_status", "tenant_id", "status"),
    )

class BillingPlans(TenantRecordMixin, Base):
    __tablename__ = "billing_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_plans_tenant_code"),
        Index("ix_billing_plans_tenant_status", "tenant_id", "status"),
    )

class BillingPrices(TenantRecordMixin, Base):
    __tablename__ = "billing_prices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_prices_tenant_code"),
        Index("ix_billing_prices_tenant_status", "tenant_id", "status"),
    )

class BillingSubscriptions(TenantRecordMixin, Base):
    __tablename__ = "billing_subscriptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_subscriptions_tenant_code"),
        Index("ix_billing_subscriptions_tenant_status", "tenant_id", "status"),
    )

class BillingTrials(TenantRecordMixin, Base):
    __tablename__ = "billing_trials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_trials_tenant_code"),
        Index("ix_billing_trials_tenant_status", "tenant_id", "status"),
    )

class BillingUsageRecords(TenantRecordMixin, Base):
    __tablename__ = "billing_usage_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_usage_records_tenant_code"),
        Index("ix_billing_usage_records_tenant_status", "tenant_id", "status"),
    )

class BillingBillingInvoices(TenantRecordMixin, Base):
    __tablename__ = "billing_billing_invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_billing_invoices_tenant_code"),
        Index("ix_billing_billing_invoices_tenant_status", "tenant_id", "status"),
    )

class BillingPaymentMethods(TenantRecordMixin, Base):
    __tablename__ = "billing_payment_methods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_payment_methods_tenant_code"),
        Index("ix_billing_payment_methods_tenant_status", "tenant_id", "status"),
    )

class BillingBillingPayments(TenantRecordMixin, Base):
    __tablename__ = "billing_billing_payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_billing_payments_tenant_code"),
        Index("ix_billing_billing_payments_tenant_status", "tenant_id", "status"),
    )

class BillingCredits(TenantRecordMixin, Base):
    __tablename__ = "billing_credits"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_credits_tenant_code"),
        Index("ix_billing_credits_tenant_status", "tenant_id", "status"),
    )

class BillingRefunds(TenantRecordMixin, Base):
    __tablename__ = "billing_refunds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_refunds_tenant_code"),
        Index("ix_billing_refunds_tenant_status", "tenant_id", "status"),
    )

class BillingDunningCases(TenantRecordMixin, Base):
    __tablename__ = "billing_dunning_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_dunning_cases_tenant_code"),
        Index("ix_billing_dunning_cases_tenant_status", "tenant_id", "status"),
    )

class SupportProblemReports(TenantRecordMixin, Base):
    __tablename__ = "support_problem_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_support_problem_reports_tenant_code"),
        Index("ix_support_problem_reports_tenant_status", "tenant_id", "status"),
    )

class SupportSupportTickets(TenantRecordMixin, Base):
    __tablename__ = "support_support_tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_support_support_tickets_tenant_code"),
        Index("ix_support_support_tickets_tenant_status", "tenant_id", "status"),
    )

class SupportTicketComments(TenantRecordMixin, Base):
    __tablename__ = "support_ticket_comments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_support_ticket_comments_tenant_code"),
        Index("ix_support_ticket_comments_tenant_status", "tenant_id", "status"),
    )

class SupportTicketAttachments(TenantRecordMixin, Base):
    __tablename__ = "support_ticket_attachments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_support_ticket_attachments_tenant_code"),
        Index("ix_support_ticket_attachments_tenant_status", "tenant_id", "status"),
    )

class SupportSlaPolicies(TenantRecordMixin, Base):
    __tablename__ = "support_sla_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_support_sla_policies_tenant_code"),
        Index("ix_support_sla_policies_tenant_status", "tenant_id", "status"),
    )

class NotificationsNotifications(TenantRecordMixin, Base):
    __tablename__ = "notifications_notifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_notifications_notifications_tenant_code"),
        Index("ix_notifications_notifications_tenant_status", "tenant_id", "status"),
    )

class NotificationsPreferences(TenantRecordMixin, Base):
    __tablename__ = "notifications_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_notifications_preferences_tenant_code"),
        Index("ix_notifications_preferences_tenant_status", "tenant_id", "status"),
    )

class NotificationsTemplates(TenantRecordMixin, Base):
    __tablename__ = "notifications_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_notifications_templates_tenant_code"),
        Index("ix_notifications_templates_tenant_status", "tenant_id", "status"),
    )

class NotificationsDeliveryAttempts(TenantRecordMixin, Base):
    __tablename__ = "notifications_delivery_attempts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_notifications_delivery_attempts_tenant_code"),
        Index("ix_notifications_delivery_attempts_tenant_status", "tenant_id", "status"),
    )

class NotificationsDigests(TenantRecordMixin, Base):
    __tablename__ = "notifications_digests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_notifications_digests_tenant_code"),
        Index("ix_notifications_digests_tenant_status", "tenant_id", "status"),
    )

class PlatformEnvironments(TenantRecordMixin, Base):
    __tablename__ = "platform_environments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_environments_tenant_code"),
        Index("ix_platform_environments_tenant_status", "tenant_id", "status"),
    )

class PlatformDeployments(TenantRecordMixin, Base):
    __tablename__ = "platform_deployments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_deployments_tenant_code"),
        Index("ix_platform_deployments_tenant_status", "tenant_id", "status"),
    )

class PlatformReleaseGates(TenantRecordMixin, Base):
    __tablename__ = "platform_release_gates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_release_gates_tenant_code"),
        Index("ix_platform_release_gates_tenant_status", "tenant_id", "status"),
    )

class PlatformLaunchDecisions(TenantRecordMixin, Base):
    __tablename__ = "platform_launch_decisions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_launch_decisions_tenant_code"),
        Index("ix_platform_launch_decisions_tenant_status", "tenant_id", "status"),
    )

class PlatformRecoveryDrills(TenantRecordMixin, Base):
    __tablename__ = "platform_recovery_drills"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_recovery_drills_tenant_code"),
        Index("ix_platform_recovery_drills_tenant_status", "tenant_id", "status"),
    )

class PlatformFailureInjectionRuns(TenantRecordMixin, Base):
    __tablename__ = "platform_failure_injection_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_failure_injection_runs_tenant_code"),
        Index("ix_platform_failure_injection_runs_tenant_status", "tenant_id", "status"),
    )

class PlatformCapacityRuns(TenantRecordMixin, Base):
    __tablename__ = "platform_capacity_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_capacity_runs_tenant_code"),
        Index("ix_platform_capacity_runs_tenant_status", "tenant_id", "status"),
    )

class PlatformSecurityFindings(TenantRecordMixin, Base):
    __tablename__ = "platform_security_findings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_security_findings_tenant_code"),
        Index("ix_platform_security_findings_tenant_status", "tenant_id", "status"),
    )

class PlatformIncidentLockouts(TenantRecordMixin, Base):
    __tablename__ = "platform_incident_lockouts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_incident_lockouts_tenant_code"),
        Index("ix_platform_incident_lockouts_tenant_status", "tenant_id", "status"),
    )

class PlatformFeatureFlags(TenantRecordMixin, Base):
    __tablename__ = "platform_feature_flags"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_feature_flags_tenant_code"),
        Index("ix_platform_feature_flags_tenant_status", "tenant_id", "status"),
    )

class PlatformConfigurationVersions(TenantRecordMixin, Base):
    __tablename__ = "platform_configuration_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_platform_configuration_versions_tenant_code"),
        Index("ix_platform_configuration_versions_tenant_status", "tenant_id", "status"),
    )
