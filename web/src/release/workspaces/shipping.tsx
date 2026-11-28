"use client";

import { useState } from "react";

import { del, errorText, get, post, upload } from "../client";
import { useLoad, usePermissions } from "../hooks";
import { Card, Notice, Workspace } from "../ui";

type Field = { name: string; label: string; secret: boolean; required: boolean; help: string };
type Carrier = { code: string; name: string; signup_url: string; instructions: string; fields: Field[] };
type CarrierAccount = { id: string; carrier: string; carrier_name: string; label: string; account_number: string | null; status: string; last_error: string | null };
type Event = { at: string | null; description: string | null; location: string | null };
type Shipment = {
  id: string;
  carrier: string;
  carrier_name: string;
  tracking_number: string;
  reference: string | null;
  direction: string;
  status: string;
  status_detail: string | null;
  estimated_delivery: string | null;
  delivered_at: string | null;
  last_location: string | null;
  last_event_at: string | null;
  last_refreshed_at: string | null;
  last_error: string | null;
  events: Event[];
};

const STATUS: Record<string, { label: string; tone: string }> = {
  pending: { label: "Waiting for tracking", tone: "neutral" },
  label_created: { label: "Label created", tone: "neutral" },
  in_transit: { label: "In transit", tone: "info" },
  out_for_delivery: { label: "Out for delivery", tone: "info" },
  delivered: { label: "Delivered", tone: "good" },
  exception: { label: "Needs attention", tone: "warn" },
  unknown: { label: "Unknown", tone: "neutral" },
};
const FILTERS: [string, string][] = [
  ["active", "On the way"],
  ["exception", "Needs attention"],
  ["delivered", "Delivered"],
  ["", "All"],
];

function day(value: string | null): string {
  return value ? new Date(value.length === 10 ? `${value}T12:00:00` : value).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) : "";
}

export function ShippingWorkspace() {
  const { can } = usePermissions();
  const [filter, setFilter] = useState("active");
  const [search, setSearch] = useState("");
  const list = useLoad(
    () => get<{ shipments: Shipment[]; counts: Record<string, number> }>("/api/v1/shipping/shipments", { status: filter || undefined, search: search || undefined }),
    `ship:${filter}:${search}`,
  );
  const carriers = useLoad(() => get<{ carriers: Carrier[]; accounts: CarrierAccount[] }>("/api/v1/shipping/carriers"), "carriers");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [expanded, setExpanded] = useState("");
  const counts = list.data?.counts ?? {};

  async function act(label: string, run: () => Promise<string>) {
    setBusy(label);
    setMessage(null);
    try {
      setMessage({ ok: true, text: await run() });
      list.reload();
      carriers.reload();
    } catch (error) {
      setMessage({ ok: false, text: errorText(error) });
    } finally {
      setBusy("");
    }
  }

  const accounts = carriers.data?.accounts ?? [];
  const onTheWay = (counts.in_transit ?? 0) + (counts.out_for_delivery ?? 0) + (counts.label_created ?? 0) + (counts.pending ?? 0);
  return (
    <Workspace title="Shipments" description="Every package from FedEx, UPS, USPS and DHL in one list, with live tracking." accent="#8b7cff">
      <div className="rwKpis">
        <article>
          <span>On the way</span>
          <strong>{onTheWay}</strong>
        </article>
        <article>
          <span>Out for delivery</span>
          <strong>{counts.out_for_delivery ?? 0}</strong>
        </article>
        <article>
          <span>Needs attention</span>
          <strong className={counts.exception ? "warnText" : ""}>{counts.exception ?? 0}</strong>
        </article>
        <article>
          <span>Delivered</span>
          <strong>{counts.delivered ?? 0}</strong>
        </article>
      </div>

      {message ? <Notice kind={message.ok ? "ok" : "error"}>{message.text}</Notice> : null}

      {can("shipping.track") ? <TrackForm busy={busy} act={act} /> : null}

      <Card
        title="Your shipments"
        aside={
          <div className="rwActions">
            <input type="search" placeholder="Tracking # or reference" aria-label="Search shipments" value={search} onChange={(e) => setSearch(e.target.value)} />
            {can("shipping.track") ? (
              <button
                type="button"
                className="rwBtn"
                disabled={!!busy}
                onClick={() => act("refresh", async () => {
                  const r = await post<{ refreshed: number; failed: number }>("/api/v1/shipping/refresh");
                  return `Updated ${r.refreshed} shipment(s)${r.failed ? `; ${r.failed} could not be updated` : ""}.`;
                })}
              >
                {busy === "refresh" ? "Updating…" : "Update all"}
              </button>
            ) : null}
          </div>
        }
      >
        <div className="rwTabs" role="tablist">
          {FILTERS.map(([value, label]) => (
            <button key={value} type="button" role="tab" aria-selected={filter === value} className={filter === value ? "on" : ""} onClick={() => setFilter(value)}>
              {label}
            </button>
          ))}
        </div>
        {list.error ? <Notice kind="error">{list.error}</Notice> : null}
        {list.data && list.data.shipments.length === 0 ? (
          <p className="rwMuted">{filter === "active" ? "Nothing on the way. Add a tracking number above." : "No shipments here."}</p>
        ) : null}
        <ul className="shipList" data-testid="shipments">
          {(list.data?.shipments ?? []).map((s) => {
            const st = STATUS[s.status] ?? STATUS.unknown;
            return (
              <li key={s.id} className="shipRow">
                <button type="button" className="shipMain" aria-expanded={expanded === s.id} onClick={() => setExpanded(expanded === s.id ? "" : s.id)}>
                  <span className={`shipStatus ${st.tone}`}>{st.label}</span>
                  <span className="shipWho">
                    <b>{s.reference || s.tracking_number}</b>
                    <span className="rwMuted small">
                      {s.carrier_name} · {s.tracking_number}
                    </span>
                  </span>
                  <span className="shipWhen">
                    {s.status === "delivered" ? (
                      <>Delivered {day(s.delivered_at)}</>
                    ) : s.estimated_delivery ? (
                      <>Arrives {day(s.estimated_delivery)}</>
                    ) : (
                      <span className="rwMuted">{s.status_detail ?? ""}</span>
                    )}
                    {s.last_location ? <span className="rwMuted small">{s.last_location}</span> : null}
                  </span>
                </button>
                {s.last_error ? <Notice kind="info">{s.last_error}</Notice> : null}
                {expanded === s.id ? (
                  <div className="shipDetail">
                    {s.events.length ? (
                      <ol className="timeline">
                        {s.events.map((e, i) => (
                          <li key={i}>
                            <b>{e.description}</b>
                            <span className="rwMuted small">
                              {e.at ? new Date(e.at).toLocaleString() : ""} {e.location ? `· ${e.location}` : ""}
                            </span>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="rwMuted">No tracking events yet.</p>
                    )}
                    {can("shipping.track") ? (
                      <div className="rwActions">
                        <button type="button" className="rwBtn" disabled={!!busy} onClick={() => act(`r-${s.id}`, async () => {
                          await post(`/api/v1/shipping/shipments/${s.id}/refresh`);
                          return `${s.tracking_number} updated.`;
                        })}>
                          Update now
                        </button>
                        <button type="button" className="rwBtn" disabled={!!busy} onClick={() => {
                          if (window.confirm(`Stop tracking ${s.tracking_number}?`)) void act(`d-${s.id}`, async () => {
                            await del(`/api/v1/shipping/shipments/${s.id}`);
                            return "Shipment removed.";
                          });
                        }}>
                          Stop tracking
                        </button>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      </Card>

      <Card
        title="Carrier accounts"
        aside={can("shipping.connect") ? (
          <button type="button" className="rwBtn primary" onClick={() => setConnecting((v) => !v)} data-testid="connect-carrier">
            Connect a carrier
          </button>
        ) : null}
      >
        <p className="rwMuted">
          Krov WorkAgent reads tracking straight from each carrier with your own carrier account, so every package — including ones you didn&apos;t ship
          through Krov WorkAgent — shows up here.
        </p>
        {connecting && carriers.data ? (
          <ConnectCarrier
            carriers={carriers.data.carriers}
            onDone={(text) => {
              setConnecting(false);
              setMessage({ ok: true, text });
              carriers.reload();
              list.reload();
            }}
          />
        ) : null}
        {accounts.length === 0 ? <p className="rwMuted">No carriers connected yet.</p> : null}
        <ul className="carrierList" data-testid="carrier-accounts">
          {accounts.map((a) => (
            <li key={a.id}>
              <b>{a.label}</b>
              <span className="rwMuted small">
                {a.carrier_name}
                {a.account_number ? ` · account ${a.account_number}` : ""} · {a.status}
              </span>
              {can("shipping.connect") ? (
                <button type="button" className="rwBtn" onClick={() => {
                  if (window.confirm(`Disconnect ${a.label}?`)) void act("dc", async () => {
                    await del(`/api/v1/shipping/accounts/${a.id}`);
                    return `${a.label} disconnected.`;
                  });
                }}>
                  Disconnect
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </Card>
    </Workspace>
  );
}

function TrackForm(props: { busy: string; act: (label: string, run: () => Promise<string>) => Promise<void> }) {
  const [number, setNumber] = useState("");
  const [carrier, setCarrier] = useState("");
  const [reference, setReference] = useState("");
  const [bulk, setBulk] = useState(false);
  return (
    <section className="rwCard trackCard">
      <form
        className="trackForm"
        aria-label="Track a package"
        onSubmit={(e) => {
          e.preventDefault();
          void props.act("track", async () => {
            const s = await post<Shipment>("/api/v1/shipping/shipments", { tracking_number: number, carrier: carrier || undefined, reference: reference || undefined });
            setNumber("");
            setReference("");
            return `Tracking ${s.carrier_name} ${s.tracking_number}: ${(STATUS[s.status] ?? STATUS.unknown).label}.`;
          });
        }}
      >
        <label className="grow">
          <span>Tracking number</span>
          <input value={number} onChange={(e) => setNumber(e.target.value)} placeholder="Paste any FedEx, UPS, USPS or DHL number" required minLength={6} data-testid="tracking-number" />
        </label>
        <label>
          <span>Carrier</span>
          <select value={carrier} onChange={(e) => setCarrier(e.target.value)} aria-label="Carrier">
            <option value="">Detect automatically</option>
            <option value="fedex">FedEx</option>
            <option value="ups">UPS</option>
            <option value="usps">USPS</option>
            <option value="dhl">DHL</option>
            <option value="demo">Demo carrier</option>
          </select>
        </label>
        <label>
          <span>Reference (optional)</span>
          <input value={reference} onChange={(e) => setReference(e.target.value)} placeholder="Order or PO number" />
        </label>
        <button type="submit" className="rwBtn primary" disabled={!!props.busy} data-testid="track-button">
          {props.busy === "track" ? "Tracking…" : "Track"}
        </button>
      </form>
      <button type="button" className="linkish" onClick={() => setBulk((v) => !v)}>
        Add many at once from a spreadsheet
      </button>
      {bulk ? (
        <div className="trackBulk">
          <p className="rwMuted">Upload a CSV with a “Tracking number” column (optional “Carrier” and “Reference” columns).</p>
          <input
            type="file"
            accept=".csv,.txt"
            aria-label="Tracking numbers CSV"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const form = new FormData();
              form.append("file", file);
              void props.act("bulk", async () => {
                const r = await upload<{ added: number; skipped: string[] }>("/api/v1/shipping/shipments/import", form);
                e.target.value = "";
                return `Added ${r.added} shipment(s).${r.skipped.length ? ` Skipped: ${r.skipped.join("; ")}` : ""}`;
              });
            }}
          />
        </div>
      ) : null}
    </section>
  );
}

function ConnectCarrier(props: { carriers: Carrier[]; onDone: (message: string) => void }) {
  const [code, setCode] = useState(props.carriers[0]?.code ?? "fedex");
  const [values, setValues] = useState<Record<string, string>>({});
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const carrier = props.carriers.find((c) => c.code === code);
  return (
    <form
      className="rwForm"
      aria-label="Connect a carrier"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try {
          const a = await post<CarrierAccount>("/api/v1/shipping/accounts", { carrier: code, label: label || undefined, credentials: values });
          props.onDone(`${a.label} connected. Its tracking now updates automatically.`);
        } catch (err) {
          setError(errorText(err));
        } finally {
          setBusy(false);
        }
      }}
    >
      <h3>Connect a carrier account</h3>
      <div className="carrierPick" role="radiogroup" aria-label="Carrier">
        {props.carriers.map((c) => (
          <button key={c.code} type="button" role="radio" aria-checked={code === c.code} className={code === c.code ? "on" : ""} onClick={() => { setCode(c.code); setValues({}); }}>
            {c.name}
          </button>
        ))}
      </div>
      {carrier ? (
        <>
          <p className="rwMuted">
            {carrier.instructions}{" "}
            <a href={carrier.signup_url} target="_blank" rel="noreferrer">
              Open the {carrier.name} developer portal
            </a>
          </p>
          <div className="rwFields">
            <label>
              <span>Name in Krov WorkAgent</span>
              <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder={`${carrier.name} (main account)`} />
            </label>
            {carrier.fields.map((f) =>
              f.name === "environment" ? (
                <label key={f.name}>
                  <span>Environment</span>
                  <select value={values.environment ?? "production"} onChange={(e) => setValues((v) => ({ ...v, environment: e.target.value }))}>
                    <option value="production">Production (real packages)</option>
                    <option value="sandbox">Sandbox (test credentials)</option>
                  </select>
                </label>
              ) : (
                <label key={f.name}>
                  <span>
                    {f.label}
                    {f.required ? "" : " (optional)"}
                  </span>
                  <input
                    type={f.secret ? "password" : "text"}
                    autoComplete="off"
                    required={f.required}
                    value={values[f.name] ?? ""}
                    onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
                  />
                </label>
              ),
            )}
          </div>
        </>
      ) : null}
      <button type="submit" className="rwBtn primary" disabled={busy}>
        {busy ? "Checking with the carrier…" : "Connect"}
      </button>
      {error ? <Notice kind="error">{error}</Notice> : null}
    </form>
  );
}
