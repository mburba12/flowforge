"use client";

import { useState } from "react";

import { post, type Row } from "../client";
import { usePostingContext } from "../context";
import { useRows } from "../hooks";
import { optionsOf, UOM_OPTIONS, useGl } from "../refs";
import { Amount, Card, Form, Grid, Table, Tabs, Workspace } from "../ui";

const TABS = [
  { id: "stock", label: "Stock" },
  { id: "products", label: "Products" },
  { id: "sites", label: "Warehouses & locations" },
];

export function InventoryWorkspace() {
  const [tab, setTab] = useState("stock");
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const key = String(version);
  const gl = useGl(key);
  const ctx = usePostingContext(gl, [{ key: "offset_account_id", label: "Adjustment offset account" }]);
  const products = useRows("products", key);
  const warehouses = useRows("warehouses", key);
  const locations = useRows("locations", key);
  const balances = useRows("inventory", key);
  const label = (rows: Row[] | null, id: unknown, f: (r: Row) => string) => {
    const r = (rows ?? []).find((x) => x.id === id);
    return r ? f(r) : String(id ?? "");
  };
  return (
    <Workspace title="Inventory" description="Products, warehouses and locations, on-hand and reserved stock, and adjustments posted to the ledger." accent="#059669">
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "stock" ? (
        <>
          {ctx.node}
          <Grid>
            <Card title="Stock on hand">
              <Table
                testId="stock-table"
                rows={balances.data}
                loading={balances.loading}
                error={balances.error}
                empty="No stock yet. Record an adjustment to receive opening stock."
                columns={[
                  { key: "product_id", label: "Product", render: (r) => label(products.data, r.product_id, (p) => `${p.sku} ${p.name}`) },
                  { key: "warehouse_id", label: "Warehouse", render: (r) => label(warehouses.data, r.warehouse_id, (w) => String(w.code)) },
                  { key: "location_id", label: "Location", render: (r) => label(locations.data, r.location_id, (l) => String(l.code)) },
                  { key: "on_hand", label: "On hand", align: "right" },
                  { key: "reserved", label: "Reserved", align: "right" },
                ]}
              />
            </Card>
            <Form
              title="Adjust stock"
              testId="adjust-form"
              permission="inventory.write"
              submitLabel="Record adjustment"
              fields={[
                { name: "product_id", label: "Product", type: "select", options: optionsOf(products.data, (p) => `${p.sku} ${p.name}`), required: true },
                { name: "warehouse_id", label: "Warehouse", type: "select", options: optionsOf(warehouses.data, (w) => `${w.code} ${w.name}`), required: true },
                { name: "location_id", label: "Location", type: "select", options: optionsOf(locations.data, (l) => String(l.code)), required: true },
                { name: "quantity", label: "Quantity (+ in / − out)", type: "number", required: true },
                { name: "unit_cost", label: "Unit cost", type: "number", required: true },
                { name: "post_to_ledger", label: "Post value to the ledger", type: "checkbox", initial: "true" },
              ]}
              onSaved={refresh}
              onSubmit={async (v) => {
                const accounting =
                  v.post_to_ledger === "true"
                    ? (() => {
                        if (!ctx.ready) throw new Error(`Choose the posting context first (${ctx.missing.join(", ")}).`);
                        return { ledger_id: ctx.values.ledger_id, period_id: ctx.values.period_id, offset_account_id: ctx.values.offset_account_id, adjustment_date: new Date().toISOString().slice(0, 10) };
                      })()
                    : undefined;
                const r = await post<{ on_hand: string }>("/api/v3b/inventory/adjust", {
                  product_id: v.product_id,
                  warehouse_id: v.warehouse_id,
                  location_id: v.location_id,
                  quantity: v.quantity,
                  unit_cost: v.unit_cost,
                  idempotency_key: `ui-${crypto.randomUUID()}`,
                  accounting,
                });
                return `Adjusted. On hand is now ${r.on_hand}.`;
              }}
            />
          </Grid>
        </>
      ) : null}
      {tab === "products" ? (
        <Grid>
          <Card title="Products">
            <Table
              testId="products-table"
              rows={products.data}
              loading={products.loading}
              error={products.error}
              columns={[
                { key: "sku", label: "SKU" },
                { key: "name", label: "Name" },
                { key: "base_uom", label: "UOM" },
                { key: "sales_price", label: "Price", align: "right", render: (r) => <Amount value={r.sales_price} /> },
                { key: "standard_cost", label: "Cost", align: "right", render: (r) => <Amount value={r.standard_cost} /> },
              ]}
            />
          </Card>
          <Form
            title="New product"
            testId="product-form"
            permission="inventory.setup"
            submitLabel="Create product"
            fields={[
              { name: "sku", label: "SKU", required: true },
              { name: "name", label: "Name", required: true },
              { name: "base_uom", label: "Unit", type: "select", options: UOM_OPTIONS, initial: "EA", required: true },
              { name: "sales_price", label: "Sales price", type: "number", required: true },
              { name: "standard_cost", label: "Standard cost", type: "number", required: true },
              { name: "inventory_account_id", label: "Inventory account", type: "select", options: gl.accountOptions("asset"), required: true },
              { name: "cogs_account_id", label: "COGS account", type: "select", options: gl.accountOptions("expense"), required: true },
            ]}
            onSaved={refresh}
            onSubmit={async (v) => {
              await post("/api/v3b/products", v);
              return `Product ${v.sku} created.`;
            }}
          />
        </Grid>
      ) : null}
      {tab === "sites" ? (
        <Grid>
          <Card title="Warehouses and locations">
            <Table rows={warehouses.data} loading={warehouses.loading} error={warehouses.error} testId="warehouses-table" columns={[{ key: "code", label: "Warehouse" }, { key: "name", label: "Name" }]} />
            <Table
              rows={locations.data}
              loading={locations.loading}
              testId="locations-table"
              columns={[
                { key: "code", label: "Location" },
                { key: "warehouse_id", label: "Warehouse", render: (r) => label(warehouses.data, r.warehouse_id, (w) => String(w.code)) },
                { key: "location_type", label: "Type" },
              ]}
            />
          </Card>
          <div className="rwStack">
            <Form
              title="New warehouse"
              testId="warehouse-form"
              permission="inventory.setup"
              submitLabel="Create warehouse"
              fields={[
                { name: "code", label: "Code", required: true },
                { name: "name", label: "Name", required: true },
              ]}
              onSaved={refresh}
              onSubmit={async (v) => {
                await post("/api/v3b/warehouses", v);
                return `Warehouse ${v.code} created.`;
              }}
            />
            <Form
              title="New location"
              testId="location-form"
              permission="inventory.setup"
              submitLabel="Create location"
              fields={[
                { name: "warehouse_id", label: "Warehouse", type: "select", options: optionsOf(warehouses.data, (w) => `${w.code} ${w.name}`), required: true },
                { name: "code", label: "Code", required: true },
              ]}
              onSaved={refresh}
              onSubmit={async (v) => {
                await post("/api/v3b/locations", v);
                return `Location ${v.code} created.`;
              }}
            />
          </div>
        </Grid>
      ) : null}
    </Workspace>
  );
}
