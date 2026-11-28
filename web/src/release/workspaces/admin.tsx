"use client";

import Link from "next/link";
import { useState } from "react";

import { del, get, patch, post, put } from "../client";
import { ALWAYS_SHOWN, HOME_SECTIONS, navGroups } from "@/lib/modules";

import { resetPermissions, useHidden, useLoad } from "../hooks";
import { SecurityCard } from "../security";
import { ActionButton, Badge, Card, Form, Grid, Notice, RequiresPermission, Table, Tabs, Workspace, useActionLog } from "../ui";

type User = { id: string; email: string; display_name: string; is_active: boolean; roles: string[] } & Record<string, unknown>;
type Role = { id: string; name: string; description: string | null; standard: boolean; permissions: string[] } & Record<string, unknown>;
type Permission = { code: string; description: string };

const TABS = [
  { id: "users", label: "Users" },
  { id: "roles", label: "Roles & permissions" },
];

/** Standard role that lets a designated person approve work they created (server: approvals.self_approve). */
const SELF_APPROVE_ROLE = "Approve own work";
const approvesOwn = (u: User, roles: Role[]) =>
  u.roles.includes("Owner") || roles.some((r) => u.roles.includes(r.name) && r.permissions.includes("approvals.self_approve"));

export function AdminWorkspace() {
  return (
    <Workspace title="Settings" description="Your connections, the people who can sign in and what each role may do." accent="#334155">
      <SecurityCard />
      <Customize />
      <Connections />
      <RequiresPermission permission="users.manage" area="Managing users and roles">
        <AdminContent />
      </RequiresPermission>
    </Workspace>
  );
}

type ConnectionStatus = { banks: number; carriers: number; shipments: number; payroll_imports: number; files: number };

/** Where each outside service connects, with its current state. */
/** Each person chooses what they see: sidebar sections and Home page parts. */
function Customize() {
  const { loaded, saving, isHidden, setHidden, showAll } = useHidden();
  const [error, setError] = useState("");
  const toggle = (key: string, shown: boolean) => {
    setError("");
    setHidden(key, !shown).catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not save."));
  };
  const box = (key: string, label: string, locked = false) => (
    <label key={key} className="rwCheck">
      <input type="checkbox" checked={locked || !isHidden(key)} disabled={!loaded || locked} onChange={(e) => toggle(key, e.target.checked)} data-testid={`show-${key}`} />
      <span>{label}</span>
    </label>
  );
  return (
    <Card
      title="Customize your screen"
      testId="customize"
      aside={
        <button type="button" className="rwBtn" disabled={!loaded} onClick={() => showAll().catch(() => setError("Could not save."))}>
          Show everything
        </button>
      }
    >
      <p className="rwMuted small">Untick anything you do not use to hide it. Only your own screen changes; everything stays included and you can show it again here any time.</p>
      <p className="rwMuted small" data-testid="customize-status" aria-live="polite">
        {saving ? "Saving…" : loaded ? "All changes saved." : ""}
      </p>
      {error ? <Notice kind="error">{error}</Notice> : null}
      <div className="rwCustomize">
        {navGroups.map((group, index) => (
          <fieldset key={index}>
            <legend>{group.label ?? (index === 0 ? "Start" : "Files and settings")}</legend>
            {group.items.map(([slug, label]) => box(`nav:${slug}`, label, ALWAYS_SHOWN.has(slug)))}
          </fieldset>
        ))}
        <fieldset>
          <legend>Home page</legend>
          {HOME_SECTIONS.map(([key, label]) => box(key, label))}
        </fieldset>
      </div>
    </Card>
  );
}

function Connections() {
  const status = useLoad(() => get<ConnectionStatus>("/api/v1/connections/status"), "settings-connections");
  const s = status.data;
  const rows: [string, string, string, string][] = [
    ["Banks", s ? (s.banks ? `${s.banks} connected` : "Not connected") : "…", "/modules/banking", "Bank accounts"],
    ["Payroll provider", s ? (s.payroll_imports ? `${s.payroll_imports} import(s) done` : "Not moved yet") : "…", "/modules/payroll", "Payroll"],
    ["Shipping carriers", s ? (s.carriers ? `${s.carriers} connected` : "Not connected") : "…", "/modules/shipping", "Shipments"],
    ["Files", s ? `${s.files} uploaded` : "…", "/modules/documents", "Files"],
  ];
  return (
    <Card title="Connections" testId="settings-connections">
      <ul className="carrierList">
        {rows.map(([name, state, href, page]) => (
          <li key={name}>
            <b>{name}</b>
            <span className="rwMuted small">{state}</span>
            <Link className="rwBtn" href={href as never}>
              Open {page}
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function AdminContent() {
  const [tab, setTab] = useState("users");
  const [version, setVersion] = useState(0);
  const refresh = () => {
    resetPermissions();
    setVersion((v) => v + 1);
  };
  const users = useLoad(() => get<User[]>("/api/v1/users"), `users:${version}`);
  const roles = useLoad(() => get<Role[]>("/api/v1/roles"), `roles:${version}`);
  return (
    <>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "users" ? <Users users={users} roles={roles} refresh={refresh} /> : null}
      {tab === "roles" ? <Roles roles={roles} refresh={refresh} /> : null}
    </>
  );
}

function Users({ users, roles, refresh }: { users: ReturnType<typeof useLoad<User[]>>; roles: ReturnType<typeof useLoad<Role[]>>; refresh: () => void }) {
  const [selectedId, setSelectedId] = useState("");
  const [role, setRole] = useState("");
  const [log, onDone] = useActionLog();
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const roleOptions = (roles.data ?? []).map((r) => ({ value: r.name, label: r.name }));
  const user = (users.data ?? []).find((u) => u.id === selectedId) ?? null;
  return (
    <Grid>
      <Card title="Users">
        <Table<User>
          testId="users-table"
          rows={users.data}
          loading={users.loading}
          error={users.error}
          selectedId={selectedId}
          onSelect={(u) => setSelectedId(u.id)}
          columns={[
            { key: "display_name", label: "Name" },
            { key: "email", label: "Email" },
            { key: "roles", label: "Roles", render: (u) => u.roles.filter((r) => r !== SELF_APPROVE_ROLE).join(", ") || "none" },
            { key: "self_approve", label: "Approves own work", render: (u) => (approvesOwn(u, roles.data ?? []) ? "Yes" : "No") },
            { key: "is_active", label: "Active", render: (u) => <Badge value={String(u.is_active)} /> },
          ]}
        />
        {user ? (
          <div className="rwSelected">
            <h3>
              {user.display_name} <Badge value={user.is_active ? "active" : "inactive"} />
            </h3>
            <div className="rwActions">
              {user.is_active ? (
                <ActionButton label="Deactivate" permission="users.manage" testId="user-deactivate" onDone={done} run={() => patch(`/api/v1/users/${user.id}`, { is_active: false })} />
              ) : (
                <ActionButton label="Activate" permission="users.manage" testId="user-activate" onDone={done} run={() => patch(`/api/v1/users/${user.id}`, { is_active: true })} />
              )}
              <label className="rwInline">
                <span>Role</span>
                <select aria-label="Role to assign" value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="">Select…</option>
                  {roleOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <ActionButton label="Assign role" permission="users.manage" testId="user-assign" disabled={!role} onDone={done} run={() => post(`/api/v1/users/${user.id}/roles`, { role })} />
              <ActionButton label="Remove role" permission="users.manage" testId="user-remove-role" disabled={!role} onDone={done} run={() => del(`/api/v1/users/${user.id}/roles/${encodeURIComponent(role)}`)} />
            </div>
            <div className="rwActions" data-testid="self-approve">
              {user.roles.includes("Owner") ? (
                <p className="rwMuted small">Owners can always approve their own journals, purchase orders, payroll runs and tax returns.</p>
              ) : user.roles.includes(SELF_APPROVE_ROLE) ? (
                <ActionButton
                  label="Require a second approver"
                  permission="users.manage"
                  testId="self-approve-off"
                  onDone={done}
                  run={() => del(`/api/v1/users/${user.id}/roles/${encodeURIComponent(SELF_APPROVE_ROLE)}`)}
                />
              ) : (
                <ActionButton
                  label="Let them approve their own work"
                  permission="users.manage"
                  testId="self-approve-on"
                  onDone={done}
                  run={() => post(`/api/v1/users/${user.id}/roles`, { role: SELF_APPROVE_ROLE })}
                />
              )}
            </div>
            {log}
          </div>
        ) : null}
      </Card>
      <Form
        title="Invite user"
        testId="user-form"
        permission="users.manage"
        submitLabel="Create user"
        fields={[
          { name: "display_name", label: "Name", required: true },
          { name: "email", label: "Email", type: "email", required: true },
          { name: "password", label: "Initial password (12+ characters)", type: "password", required: true },
          { name: "role", label: "Role", type: "select", options: roleOptions, required: true },
        ]}
        onSaved={refresh}
        onSubmit={async (v) => {
          const created = await post<User>("/api/v1/users", { display_name: v.display_name, email: v.email, password: v.password, roles: [v.role] });
          return `User ${created.email} created with role ${v.role}. Share the initial password with them securely.`;
        }}
      />
    </Grid>
  );
}

function Roles({ roles, refresh }: { roles: ReturnType<typeof useLoad<Role[]>>; refresh: () => void }) {
  const catalog = useLoad(() => get<Permission[]>("/api/v1/permissions"), "catalog");
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState<Set<string> | null>(null);
  const [log, onDone] = useActionLog();
  const role = (roles.data ?? []).find((r) => r.id === selectedId) ?? null;
  const chosen = draft ?? new Set(role?.permissions ?? []);
  return (
    <Grid>
      <Card title="Roles">
        <Table<Role>
          testId="roles-table"
          rows={roles.data}
          loading={roles.loading}
          error={roles.error}
          selectedId={selectedId}
          onSelect={(r) => {
            setSelectedId(r.id);
            setDraft(null);
          }}
          columns={[
            { key: "name", label: "Role" },
            { key: "standard", label: "Type", render: (r) => (r.standard ? "standard" : "custom") },
            { key: "permissions", label: "Permissions", render: (r) => String(r.permissions.length) },
          ]}
        />
        {role ? (
          <div className="rwSelected">
            <h3>{role.name}</h3>
            {role.name === "Owner" ? <Notice kind="info">The Owner role always has every permission.</Notice> : null}
            <div className="rwPerms">
              {(catalog.data ?? [])
                .filter((p) => p.code !== "platform.tenants.create")
                .map((p) => (
                  <label key={p.code} title={p.description}>
                    <input
                      type="checkbox"
                      disabled={role.name === "Owner"}
                      checked={chosen.has(p.code)}
                      onChange={(e) => {
                        const next = new Set(chosen);
                        if (e.target.checked) next.add(p.code);
                        else next.delete(p.code);
                        setDraft(next);
                      }}
                    />
                    <span>{p.code}</span>
                  </label>
                ))}
            </div>
            <div className="rwActions">
              <ActionButton
                label="Save permissions"
                permission="roles.manage"
                testId="role-save"
                primary
                disabled={role.name === "Owner" || draft === null}
                onDone={(m, ok) => {
                  onDone(m, ok);
                  if (ok) {
                    setDraft(null);
                    refresh();
                  }
                }}
                run={() => put(`/api/v1/roles/${role.id}/permissions`, { permissions: [...chosen].sort() })}
              />
            </div>
            {log}
          </div>
        ) : null}
      </Card>
      <Form
        title="New custom role"
        testId="role-form"
        permission="roles.manage"
        submitLabel="Create role"
        fields={[
          { name: "name", label: "Name", required: true },
          { name: "description", label: "Description" },
        ]}
        onSaved={refresh}
        onSubmit={async (v) => {
          await post("/api/v1/roles", { name: v.name, description: v.description || null });
          return `Role ${v.name} created. Select it to choose its permissions.`;
        }}
      />
    </Grid>
  );
}
