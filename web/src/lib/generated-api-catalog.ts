export type ApiParameter = { name: string; location: string; required: boolean; schema: Record<string, unknown> };
export type ApiOperation = { method: string; path: string; operationId: string; summary: string; description: string; tags: string[]; parameters: ApiParameter[]; requestSchema: unknown; frontendReferenced: boolean };

export const apiOperations: ApiOperation[] = [
  {
    "method": "GET",
    "path": "/api/v1/audit",
    "operationId": "audit_api_v1_audit_get",
    "summary": "Audit",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/auth/bootstrap",
    "operationId": "bootstrap_api_v1_auth_bootstrap_post",
    "summary": "Bootstrap",
    "description": "",
    "tags": [
      "auth"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/BootstrapRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/auth/login",
    "operationId": "login_api_v1_auth_login_post",
    "summary": "Login",
    "description": "",
    "tags": [
      "auth"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LoginRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/documents",
    "operationId": "document_api_v1_documents_post",
    "summary": "Document",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/DocumentCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v1/health",
    "operationId": "health_api_v1_health_get",
    "summary": "Health",
    "description": "",
    "tags": [
      "health"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/integrations",
    "operationId": "integration_api_v1_integrations_post",
    "summary": "Integration",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/IntegrationCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v1/me",
    "operationId": "me_api_v1_me_get",
    "summary": "Me",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/notifications",
    "operationId": "notification_api_v1_notifications_post",
    "summary": "Notification",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/NotificationCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/roles",
    "operationId": "create_role_api_v1_roles_post",
    "summary": "Create Role",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/RoleCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/support/problem-reports",
    "operationId": "submit_problem_report_api_v1_support_problem_reports_post",
    "summary": "Submit Problem Report",
    "description": "",
    "tags": [
      "support"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/ProblemReport"
    },
    "frontendReferenced": true
  },
  {
    "method": "GET",
    "path": "/api/v1/tenants",
    "operationId": "list_tenants_api_v1_tenants_get",
    "summary": "List Tenants",
    "description": "",
    "tags": [
      "tenants"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/tenants",
    "operationId": "create_tenant_api_v1_tenants_post",
    "summary": "Create Tenant",
    "description": "",
    "tags": [
      "tenants"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TenantCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v1/workflows",
    "operationId": "workflow_api_v1_workflows_post",
    "summary": "Workflow",
    "description": "",
    "tags": [
      "platform"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/WorkflowCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/accounting-periods",
    "operationId": "create_period_api_v2_accounting_periods_post",
    "summary": "Create Period",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/PeriodCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/accounts",
    "operationId": "create_account_api_v2_accounts_post",
    "summary": "Create Account",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/AccountCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/currencies",
    "operationId": "create_currency_api_v2_currencies_post",
    "summary": "Create Currency",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/CurrencyCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/fiscal-calendars",
    "operationId": "create_calendar_api_v2_fiscal_calendars_post",
    "summary": "Create Calendar",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/CalendarCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/journals",
    "operationId": "create_journal_api_v2_journals_post",
    "summary": "Create Journal",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/JournalCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/journals/{journal_id}/approve",
    "operationId": "approve_journal_api_v2_journals__journal_id__approve_post",
    "summary": "Approve Journal",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [
      {
        "name": "journal_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Journal Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/journals/{journal_id}/post",
    "operationId": "post_journal_api_v2_journals__journal_id__post_post",
    "summary": "Post Journal",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [
      {
        "name": "journal_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Journal Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/ledgers",
    "operationId": "create_ledger_api_v2_ledgers_post",
    "summary": "Create Ledger",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LedgerCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/organization-units",
    "operationId": "create_unit_api_v2_organization_units_post",
    "summary": "Create Unit",
    "description": "",
    "tags": [
      "phase2a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/OrganizationUnitCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/organizations",
    "operationId": "create_organization_api_v2_organizations_post",
    "summary": "Create Organization",
    "description": "",
    "tags": [
      "phase2a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/OrganizationCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/parties/search",
    "operationId": "search_parties_api_v2_parties_search_post",
    "summary": "Search Parties",
    "description": "",
    "tags": [
      "phase2a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/SearchRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v2/parties/{party_id}",
    "operationId": "get_party_api_v2_parties__party_id__get",
    "summary": "Get Party",
    "description": "",
    "tags": [
      "phase2a"
    ],
    "parameters": [
      {
        "name": "party_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Party Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v2/people",
    "operationId": "create_person_api_v2_people_post",
    "summary": "Create Person",
    "description": "",
    "tags": [
      "phase2a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/PersonCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v2/trial-balance",
    "operationId": "trial_balance_api_v2_trial_balance_get",
    "summary": "Trial Balance",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [
      {
        "name": "ledger_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ledger Id"
        }
      },
      {
        "name": "period_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Period Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/ap/open-items/{open_item_id}/pay",
    "operationId": "pay_api_v3_ap_open_items__open_item_id__pay_post",
    "summary": "Pay",
    "description": "",
    "tags": [
      "phase3a-final"
    ],
    "parameters": [
      {
        "name": "open_item_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Open Item Id"
        }
      },
      {
        "name": "amount",
        "location": "query",
        "required": true,
        "schema": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "string"
            }
          ],
          "title": "Amount"
        }
      },
      {
        "name": "payment_date",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "date",
          "title": "Payment Date"
        }
      },
      {
        "name": "ledger_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ledger Id"
        }
      },
      {
        "name": "period_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Period Id"
        }
      },
      {
        "name": "ap_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ap Account Id"
        }
      },
      {
        "name": "cash_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Cash Account Id"
        }
      },
      {
        "name": "currency_code",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "title": "Currency Code"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/ap/reconcile",
    "operationId": "reconcile_api_v3_ap_reconcile_post",
    "summary": "Reconcile",
    "description": "",
    "tags": [
      "phase3a-final"
    ],
    "parameters": [
      {
        "name": "ledger_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ledger Id"
        }
      },
      {
        "name": "period_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Period Id"
        }
      },
      {
        "name": "ap_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ap Account Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v3/final/reconcile",
    "operationId": "reconcile_api_v3_final_reconcile_get",
    "summary": "Reconcile",
    "description": "",
    "tags": [
      "phase3-final"
    ],
    "parameters": [
      {
        "name": "ap_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ap Account Id"
        }
      },
      {
        "name": "ar_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ar Account Id"
        }
      },
      {
        "name": "inventory_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Inventory Account Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/goods-receipts",
    "operationId": "receipt_api_v3_goods_receipts_post",
    "summary": "Receipt",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/flowforge__phase3a__schemas__ReceiptCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/purchase-orders",
    "operationId": "purchase_order_api_v3_purchase_orders_post",
    "summary": "Purchase Order",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/POCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/purchase-orders/{po_id}/approve",
    "operationId": "approve_api_v3_purchase_orders__po_id__approve_post",
    "summary": "Approve",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [
      {
        "name": "po_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Po Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/purchase-orders/{po_id}/submit",
    "operationId": "submit_api_v3_purchase_orders__po_id__submit_post",
    "summary": "Submit",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [
      {
        "name": "po_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Po Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/vendor-invoices",
    "operationId": "invoice_api_v3_vendor_invoices_post",
    "summary": "Invoice",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/InvoiceCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/vendor-invoices/{invoice_id}/match",
    "operationId": "match_invoice_api_v3_vendor_invoices__invoice_id__match_post",
    "summary": "Match Invoice",
    "description": "",
    "tags": [
      "phase3a-integration"
    ],
    "parameters": [
      {
        "name": "invoice_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Invoice Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/vendor-invoices/{invoice_id}/post",
    "operationId": "post_invoice_api_v3_vendor_invoices__invoice_id__post_post",
    "summary": "Post Invoice",
    "description": "",
    "tags": [
      "phase3a-integration"
    ],
    "parameters": [
      {
        "name": "invoice_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Invoice Id"
        }
      },
      {
        "name": "ledger_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ledger Id"
        }
      },
      {
        "name": "period_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Period Id"
        }
      },
      {
        "name": "ap_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Ap Account Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3/vendors",
    "operationId": "vendor_api_v3_vendors_post",
    "summary": "Vendor",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/VendorCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/customers",
    "operationId": "create_customer_api_v3b_customers_post",
    "summary": "Create Customer",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/CustomerCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/inventory/adjust",
    "operationId": "adjust_inventory_api_v3b_inventory_adjust_post",
    "summary": "Adjust Inventory",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/InventoryAdjust"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/locations",
    "operationId": "create_location_api_v3b_locations_post",
    "summary": "Create Location",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LocationCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/orders",
    "operationId": "create_order_api_v3b_orders_post",
    "summary": "Create Order",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/OrderCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/orders/{order_id}/reserve",
    "operationId": "reserve_order_api_v3b_orders__order_id__reserve_post",
    "summary": "Reserve Order",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [
      {
        "name": "order_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Order Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/orders/{order_id}/ship-invoice",
    "operationId": "ship_and_invoice_order_api_v3b_orders__order_id__ship_invoice_post",
    "summary": "Ship And Invoice Order",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [
      {
        "name": "order_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Order Id"
        }
      },
      {
        "name": "ship_date",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "date",
          "title": "Ship Date"
        }
      },
      {
        "name": "due_date",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "date",
          "title": "Due Date"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/products",
    "operationId": "create_product_api_v3b_products_post",
    "summary": "Create Product",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/ProductCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/receipts",
    "operationId": "create_receipt_api_v3b_receipts_post",
    "summary": "Create Receipt",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/flowforge__phase3b__schemas__ReceiptCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v3b/warehouses",
    "operationId": "create_warehouse_api_v3b_warehouses_post",
    "summary": "Create Warehouse",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/WarehouseCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/ai/uploads/inspect",
    "operationId": "inspect_api_v4_ai_uploads_inspect_post",
    "summary": "Inspect",
    "description": "",
    "tags": [
      "phase4f-ai"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/UploadInspection"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/entities",
    "operationId": "create_api_v4_entities_post",
    "summary": "Create",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/EntityCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/entities/match",
    "operationId": "match_api_v4_entities_match_post",
    "summary": "Match",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/MatchRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/entities/merge-proposals",
    "operationId": "merge_api_v4_entities_merge_proposals_post",
    "summary": "Merge",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/MergeProposalCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/entities/merge-proposals/{proposal_id}/approve",
    "operationId": "approve_api_v4_entities_merge_proposals__proposal_id__approve_post",
    "summary": "Approve",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [
      {
        "name": "proposal_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Proposal Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/entities/relationships",
    "operationId": "relationship_api_v4_entities_relationships_post",
    "summary": "Relationship",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/RelationshipCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v4/entities/{entity_id}",
    "operationId": "get_api_v4_entities__entity_id__get",
    "summary": "Get",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [
      {
        "name": "entity_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Entity Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/entities/{entity_id}/lineage",
    "operationId": "lineage_api_v4_entities__entity_id__lineage_post",
    "summary": "Lineage",
    "description": "",
    "tags": [
      "phase4d-entities"
    ],
    "parameters": [
      {
        "name": "entity_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Entity Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/ReferenceCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/reconciliations/amount",
    "operationId": "amount_api_v4_reconciliations_amount_post",
    "summary": "Amount",
    "description": "",
    "tags": [
      "phase4e-reconciliation"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/AmountReconciliationRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4/reconciliations/commerce-to-cash",
    "operationId": "commerce_api_v4_reconciliations_commerce_to_cash_post",
    "summary": "Commerce",
    "description": "",
    "tags": [
      "phase4e-reconciliation"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/CommerceToCashRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/benefit-plans",
    "operationId": "benefit_plan_api_v4a_benefit_plans_post",
    "summary": "Benefit Plan",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/BenefitPlanCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/leave-requests",
    "operationId": "leave_request_api_v4a_leave_requests_post",
    "summary": "Leave Request",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LeaveRequestCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/leave-types",
    "operationId": "leave_type_api_v4a_leave_types_post",
    "summary": "Leave Type",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LeaveTypeCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/pay-groups",
    "operationId": "pay_group_api_v4a_pay_groups_post",
    "summary": "Pay Group",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/PayGroupCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/pay-periods",
    "operationId": "pay_period_api_v4a_pay_periods_post",
    "summary": "Pay Period",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/PayPeriodCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/payroll/runs",
    "operationId": "create_run_api_v4a_payroll_runs_post",
    "summary": "Create Run",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/PayrollRunCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/payroll/runs/{run_id}/approve",
    "operationId": "approve_api_v4a_payroll_runs__run_id__approve_post",
    "summary": "Approve",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [
      {
        "name": "run_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Run Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/payroll/runs/{run_id}/calculate",
    "operationId": "calculate_api_v4a_payroll_runs__run_id__calculate_post",
    "summary": "Calculate",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [
      {
        "name": "run_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Run Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/PayrollCalculate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/payroll/runs/{run_id}/payments",
    "operationId": "payment_api_v4a_payroll_runs__run_id__payments_post",
    "summary": "Payment",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [
      {
        "name": "run_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Run Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/PayrollPaymentCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/payroll/runs/{run_id}/post",
    "operationId": "post_api_v4a_payroll_runs__run_id__post_post",
    "summary": "Post",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [
      {
        "name": "run_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Run Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/PayrollPostAccounts"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/payroll/runs/{run_id}/reconcile",
    "operationId": "reconcile_api_v4a_payroll_runs__run_id__reconcile_post",
    "summary": "Reconcile",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [
      {
        "name": "run_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Run Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/time-entries",
    "operationId": "time_entry_api_v4a_time_entries_post",
    "summary": "Time Entry",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TimeEntryCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/time-entries/{entry_id}/approve",
    "operationId": "approve_time_api_v4a_time_entries__entry_id__approve_post",
    "summary": "Approve Time",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [
      {
        "name": "entry_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Entry Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/work-locations",
    "operationId": "create_location_api_v4a_work_locations_post",
    "summary": "Create Location",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/WorkLocationCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/work-schedules",
    "operationId": "schedule_api_v4a_work_schedules_post",
    "summary": "Schedule",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/ScheduleCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/workers",
    "operationId": "create_worker_api_v4a_workers_post",
    "summary": "Create Worker",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/WorkerCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/workers/{worker_id}/assignments",
    "operationId": "assign_api_v4a_workers__worker_id__assignments_post",
    "summary": "Assign",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [
      {
        "name": "worker_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Worker Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/AssignmentCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/workers/{worker_id}/bank-accounts",
    "operationId": "bank_account_api_v4a_workers__worker_id__bank_accounts_post",
    "summary": "Bank Account",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [
      {
        "name": "worker_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Worker Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/BankAccountCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/workers/{worker_id}/benefit-enrollments",
    "operationId": "enroll_api_v4a_workers__worker_id__benefit_enrollments_post",
    "summary": "Enroll",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [
      {
        "name": "worker_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Worker Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/BenefitEnrollmentCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/workers/{worker_id}/compensation",
    "operationId": "compensation_api_v4a_workers__worker_id__compensation_post",
    "summary": "Compensation",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [
      {
        "name": "worker_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Worker Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/CompensationCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4a/workers/{worker_id}/tax-profiles",
    "operationId": "tax_profile_api_v4a_workers__worker_id__tax_profiles_post",
    "summary": "Tax Profile",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [
      {
        "name": "worker_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Worker Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxProfileCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/calculate",
    "operationId": "calculate_api_v4b_calculate_post",
    "summary": "Calculate",
    "description": "",
    "tags": [
      "phase4b-tax"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxCalculate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/jurisdictions",
    "operationId": "jurisdiction_api_v4b_jurisdictions_post",
    "summary": "Jurisdiction",
    "description": "",
    "tags": [
      "phase4b-tax"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/JurisdictionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/liabilities",
    "operationId": "create_liability_api_v4b_liabilities_post",
    "summary": "Create Liability",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxLiabilityCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/notices",
    "operationId": "create_notice_api_v4b_notices_post",
    "summary": "Create Notice",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxNoticeCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/notices/{notice_id}/resolve",
    "operationId": "resolve_notice_api_v4b_notices__notice_id__resolve_post",
    "summary": "Resolve Notice",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [
      {
        "name": "notice_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Notice Id"
        }
      },
      {
        "name": "resolution",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "minLength": 1,
          "title": "Resolution"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/reconcile",
    "operationId": "reconcile_tax_api_v4b_reconcile_post",
    "summary": "Reconcile Tax",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [
      {
        "name": "authority_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Authority Id"
        }
      },
      {
        "name": "tax_payable_account_id",
        "location": "query",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Tax Payable Account Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/returns",
    "operationId": "create_return_api_v4b_returns_post",
    "summary": "Create Return",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxReturnCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/returns/{return_id}/approve",
    "operationId": "approve_return_api_v4b_returns__return_id__approve_post",
    "summary": "Approve Return",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [
      {
        "name": "return_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Return Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/returns/{return_id}/remit",
    "operationId": "remit_return_api_v4b_returns__return_id__remit_post",
    "summary": "Remit Return",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [
      {
        "name": "return_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Return Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxRemittanceCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/tax-rules",
    "operationId": "rule_api_v4b_tax_rules_post",
    "summary": "Rule",
    "description": "",
    "tags": [
      "phase4b-tax"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxRuleCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4b/worker-elections",
    "operationId": "election_api_v4b_worker_elections_post",
    "summary": "Election",
    "description": "",
    "tags": [
      "phase4b-tax"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TaxElectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "PUT",
    "path": "/api/v4c/accounts/{account_id}/gl-mapping",
    "operationId": "mapping_api_v4c_accounts__account_id__gl_mapping_put",
    "summary": "Mapping",
    "description": "",
    "tags": [
      "phase4c-banking"
    ],
    "parameters": [
      {
        "name": "account_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Account Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/GLMappingCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/commerce/connections",
    "operationId": "connect_api_v4c_commerce_connections_post",
    "summary": "Connect",
    "description": "",
    "tags": [
      "phase4c-commerce"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/CommerceConnectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/commerce/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_commerce_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-commerce"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/CommerceSyncRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/commerce/connections/{connection_id}/webhooks",
    "operationId": "webhook_api_v4c_commerce_connections__connection_id__webhooks_post",
    "summary": "Webhook",
    "description": "",
    "tags": [
      "phase4c-commerce"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/CommerceWebhookIngest"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v4c/commerce/providers",
    "operationId": "providers_api_v4c_commerce_providers_get",
    "summary": "Providers",
    "description": "",
    "tags": [
      "phase4c-commerce"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/connections/exchange",
    "operationId": "exchange_api_v4c_connections_exchange_post",
    "summary": "Exchange",
    "description": "",
    "tags": [
      "phase4c-banking"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/TokenExchange"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/connections/link-session",
    "operationId": "link_api_v4c_connections_link_session_post",
    "summary": "Link",
    "description": "",
    "tags": [
      "phase4c-banking"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LinkSessionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-banking"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/engagement/connections",
    "operationId": "connect_api_v4c_engagement_connections_post",
    "summary": "Connect",
    "description": "",
    "tags": [
      "phase4c-engagement"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/EngagementConnectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/engagement/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_engagement_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-engagement"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/EngagementSyncRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/engagement/connections/{connection_id}/webhooks",
    "operationId": "webhook_api_v4c_engagement_connections__connection_id__webhooks_post",
    "summary": "Webhook",
    "description": "",
    "tags": [
      "phase4c-engagement"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/EngagementWebhookIngest"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v4c/engagement/providers",
    "operationId": "providers_api_v4c_engagement_providers_get",
    "summary": "Providers",
    "description": "",
    "tags": [
      "phase4c-engagement"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/finance/connections",
    "operationId": "connect_api_v4c_finance_connections_post",
    "summary": "Connect",
    "description": "",
    "tags": [
      "phase4c-finance"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/FinanceConnectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/finance/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_finance_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-finance"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/FinanceSyncRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/finance/connections/{connection_id}/webhooks",
    "operationId": "webhook_api_v4c_finance_connections__connection_id__webhooks_post",
    "summary": "Webhook",
    "description": "",
    "tags": [
      "phase4c-finance"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/FinanceWebhookIngest"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v4c/finance/providers",
    "operationId": "providers_api_v4c_finance_providers_get",
    "summary": "Providers",
    "description": "",
    "tags": [
      "phase4c-finance"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/logistics/connections",
    "operationId": "connect_api_v4c_logistics_connections_post",
    "summary": "Connect",
    "description": "",
    "tags": [
      "phase4c-logistics"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/LogisticsConnectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/logistics/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_logistics_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-logistics"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/LogisticsSyncRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/logistics/connections/{connection_id}/webhooks",
    "operationId": "webhook_api_v4c_logistics_connections__connection_id__webhooks_post",
    "summary": "Webhook",
    "description": "",
    "tags": [
      "phase4c-logistics"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/LogisticsWebhookIngest"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v4c/logistics/providers",
    "operationId": "providers_api_v4c_logistics_providers_get",
    "summary": "Providers",
    "description": "",
    "tags": [
      "phase4c-logistics"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/payments/connections",
    "operationId": "connect_api_v4c_payments_connections_post",
    "summary": "Connect",
    "description": "",
    "tags": [
      "phase4c-payments"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/PaymentConnectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/payments/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_payments_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-payments"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/PaymentSyncRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/payments/connections/{connection_id}/webhooks",
    "operationId": "webhook_api_v4c_payments_connections__connection_id__webhooks_post",
    "summary": "Webhook",
    "description": "",
    "tags": [
      "phase4c-payments"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/WebhookIngest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/transactions/manual",
    "operationId": "manual_api_v4c_transactions_manual_post",
    "summary": "Manual",
    "description": "",
    "tags": [
      "phase4c-banking"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/ManualTransactionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/workforce/connections",
    "operationId": "connect_api_v4c_workforce_connections_post",
    "summary": "Connect",
    "description": "",
    "tags": [
      "phase4c-workforce"
    ],
    "parameters": [],
    "requestSchema": {
      "$ref": "#/components/schemas/WorkforceConnectionCreate"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/workforce/connections/{connection_id}/sync",
    "operationId": "sync_api_v4c_workforce_connections__connection_id__sync_post",
    "summary": "Sync",
    "description": "",
    "tags": [
      "phase4c-workforce"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/WorkforceSyncRequest"
    },
    "frontendReferenced": false
  },
  {
    "method": "POST",
    "path": "/api/v4c/workforce/connections/{connection_id}/webhooks",
    "operationId": "webhook_api_v4c_workforce_connections__connection_id__webhooks_post",
    "summary": "Webhook",
    "description": "",
    "tags": [
      "phase4c-workforce"
    ],
    "parameters": [
      {
        "name": "connection_id",
        "location": "path",
        "required": true,
        "schema": {
          "type": "string",
          "format": "uuid",
          "title": "Connection Id"
        }
      }
    ],
    "requestSchema": {
      "$ref": "#/components/schemas/WorkforceWebhookIngest"
    },
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/api/v4c/workforce/providers",
    "operationId": "providers_api_v4c_workforce_providers_get",
    "summary": "Providers",
    "description": "",
    "tags": [
      "phase4c-workforce"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase1/status",
    "operationId": "phase1_status_phase1_status_get",
    "summary": "Phase1 Status",
    "description": "",
    "tags": [
      "phase1"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase1a/status",
    "operationId": "status_phase1a_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase1a"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase1b/health",
    "operationId": "health_phase1b_health_get",
    "summary": "Health",
    "description": "",
    "tags": [
      "phase1b"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase2a/status",
    "operationId": "status_phase2a_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase2a"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase2b/status",
    "operationId": "status_phase2b_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase2b"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase3/status",
    "operationId": "status_phase3_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase3-final"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase3a/status",
    "operationId": "status_phase3a_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase3a"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase3b/status",
    "operationId": "status_phase3b_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase3b"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4d/status",
    "operationId": "status_phase4_4d_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4d"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4e/status",
    "operationId": "status_phase4_4e_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4e"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4f/status",
    "operationId": "status_phase4_4f_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4f"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4g/status",
    "operationId": "status_phase4_4g_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4g"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4h/status",
    "operationId": "status_phase4_4h_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4h"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4i/status",
    "operationId": "status_phase4_4i_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4i"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4/4j/status",
    "operationId": "status_phase4_4j_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4-4j"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4a/stage2/status",
    "operationId": "status_phase4a_stage2_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4a-time"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4a/stage3/status",
    "operationId": "status_phase4a_stage3_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4a-payroll"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4a/status",
    "operationId": "status_phase4a_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4a"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4b/stage2/status",
    "operationId": "status_phase4b_stage2_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4b-filing"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4b/status",
    "operationId": "status_phase4b_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4b-tax"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/stage2/status",
    "operationId": "status_phase4c_stage2_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-payments"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/stage3/status",
    "operationId": "status_phase4c_stage3_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-commerce"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/stage4/status",
    "operationId": "status_phase4c_stage4_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-logistics"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/stage5/status",
    "operationId": "status_phase4c_stage5_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-finance"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/stage6/status",
    "operationId": "status_phase4c_stage6_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-workforce"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/stage7/status",
    "operationId": "status_phase4c_stage7_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-engagement"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase4c/status",
    "operationId": "status_phase4c_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase4c-banking"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": false
  },
  {
    "method": "GET",
    "path": "/phase5a/status",
    "operationId": "status_phase5a_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase5a"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": true
  },
  {
    "method": "GET",
    "path": "/phase5b/status",
    "operationId": "status_phase5b_status_get",
    "summary": "Status",
    "description": "",
    "tags": [
      "phase5b"
    ],
    "parameters": [],
    "requestSchema": null,
    "frontendReferenced": true
  }
];
export const apiTags = [...new Set(apiOperations.flatMap((item) => item.tags))].sort();
