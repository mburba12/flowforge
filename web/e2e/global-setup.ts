import { randomBytes } from "node:crypto";

// Creates a throwaway tenant and owner for this browser run. Credentials live
// only in this process's environment (inherited by test workers) and are never
// written to disk. Tenants are prefixed "e2e-" so acceptance cleanup can find them.
export default async function globalSetup(): Promise<void> {
  const api = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8001";
  const slug = `e2e-${Date.now().toString(36)}-${randomBytes(3).toString("hex")}`;
  const email = `owner-${slug}@example.com`;
  const password = `E2e-${randomBytes(16).toString("hex")}`;

  const response = await fetch(`${api}/api/v1/auth/bootstrap`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({
      tenant: { name: "Browser Acceptance", slug },
      email,
      password,
      display_name: "Browser Acceptance Owner",
    }),
  });
  if (response.status !== 201) {
    throw new Error(`Browser acceptance bootstrap failed: HTTP ${response.status} ${await response.text()}`);
  }

  process.env.E2E_TENANT = slug;
  process.env.E2E_EMAIL = email;
  process.env.E2E_PASSWORD = password;

  // Second user for approvals and segregation-of-duties flows.
  const { access_token: ownerToken } = (await response.json()) as { access_token: string };
  const approverEmail = `approver-${slug}@example.com`;
  const approver = await fetch(`${api}/api/v1/users`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${ownerToken}` },
    body: JSON.stringify({ email: approverEmail, display_name: "Browser Approver", password, roles: ["Manager"] }),
  });
  if (approver.status !== 201) {
    throw new Error(`Browser acceptance approver creation failed: HTTP ${approver.status} ${await approver.text()}`);
  }
  process.env.E2E_APPROVER_EMAIL = approverEmail;
}
