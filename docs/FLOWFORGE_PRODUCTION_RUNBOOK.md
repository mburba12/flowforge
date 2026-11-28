# FlowForge production runbook

FlowForge runs as one Docker Compose project, **`flowforge`**, defined in
`compose.production.yml`. Secrets live in `.env.production` (gitignored, generated
by `Install-FlowForge.ps1`; never commit or share it).

| Service | Purpose | Host port |
|---|---|---|
| `web` | Next.js app (Krov WorkAgent) | `127.0.0.1:3000` |
| `api` | FastAPI, runs as the restricted role `flowforge_app` (no superuser, no RLS bypass) | `127.0.0.1:8000` |
| `db` | PostgreSQL 16, volume `flowforge_flowforge_pgdata`; forced row-level security on every tenant table | `127.0.0.1:5435` |
| `migrate` | one-shot `alembic upgrade head` as the database owner, runs before `api` starts | — |
| `redis`, `azurite`, `mailpit` | supporting services (internal only; the API does not use them yet) | — |

`docker-compose.yml` is the **isolated test stack** used by the acceptance scripts.
It is never production. Do not point acceptance scripts at the `flowforge` project.

All commands below are run from the project folder in PowerShell.

## Everyday operations

Start (or apply a new build):

```powershell
.\scripts\production\Start-FlowForge.ps1 -Build
```

Stop (data is always kept; never use `docker compose down -v`):

```powershell
.\scripts\production\Stop-FlowForge.ps1
```

Status and health:

```powershell
.\scripts\production\Status-FlowForge.ps1
```

Full read-only verification (services, migrations, RLS, runtime role, endpoints,
reference data, tenant isolation, server errors):

```powershell
.\scripts\production\Test-FlowForgeStack.ps1
```

After a Windows reboot, Docker Desktop starts the stack automatically
(`restart: unless-stopped`). If Docker Desktop is not set to start at sign-in,
start it, then run `Start-FlowForge.ps1`.

## Passwords

Rotate the administrator password (hidden prompt; hashed inside the API container):

```powershell
.\scripts\production\Set-FlowForgeAdminPassword.ps1 -Email <your sign-in email>
```

The cutover copied your existing password hash, so the temporary recovery password
still works until you run this. Run it, then delete the plaintext password line from
`release-20261127-154058\release-manifest.txt`.

## Backup and restore

Backups are verified, **encrypted** (AES-256-GCM with `FLOWFORGE_BACKUP_KEY`) and, when
`FLOWFORGE_BACKUP_OFFSITE_DIR` is set, copied off this computer. A daily backup runs at
2:30 AM (Windows Task Scheduler, "Krov WorkAgent daily backup"); daily backups are kept 30
days. Keep the backup key in your password manager: without it no backup can be opened.

```powershell
.\scripts\production\Backup-FlowForge.ps1 -Label manual
```

Restore into a scratch database to inspect a backup (never over production without a fresh
backup first). Decrypt it first; `$env:FLOWFORGE_BACKUP_KEY` must hold the backup key:

```powershell
.\.venv\Scripts\python.exe scripts\production\ffcrypt.py decrypt <backup.dump.enc> var\tmp\restore.dump
```

```powershell
docker cp var\tmp\restore.dump flowforge-db-1:/tmp/restore.dump
docker exec flowforge-db-1 createdb -U flowforge_owner restore_check
docker exec flowforge-db-1 pg_restore -U flowforge_owner -d restore_check --no-owner /tmp/restore.dump
```

Delete `var\tmp\restore.dump` and `/tmp/restore.dump` when done.

## Security

Switch everything on (run once after the security release is live; asks for your new admin
password last):

```powershell
.\scripts\production\Complete-FlowForgeSecurity.ps1
```

What is protected and how:

| What | Protection |
|---|---|
| Passwords | Argon2 hashes; never stored or logged in plain text |
| Bank, Gusto and carrier credentials; worker bank and routing numbers; tax registration numbers; uploaded files; authenticator secrets | Encrypted in the database (AES-256-GCM, `FLOWFORGE_CREDENTIALS_KEY`), bound to their row or column |
| Card details | Never reach the server (Stripe); only Stripe ids, brand, last 4 and expiry |
| Recovery codes, reset and confirmation links | Stored only as SHA-256 hashes; links expire (30 minutes / 7 days) and work once |
| Backups and old exports | Encrypted files; plain copies removed after checking |
| Settings file and backup folders | Readable only by your Windows account |
| Database and Docker's disk | Windows device encryption / BitLocker (turn it on: Settings > Privacy & security > Device encryption) |
| Traffic | HTTPS end to end through Cloudflare; ports listen on this computer only |

Sign-in: owners and anyone who manages users or billing must use two-step sign-in (an
authenticator app; 10 one-time recovery codes). Signing out ends the session on the server;
changing or resetting a password ends every other session. Sign-in, sign-up, code entry and
password reset are rate-limited; sign-up and reset can require Cloudflare Turnstile
(`FLOWFORGE_TURNSTILE_SITE_KEY` / `_SECRET`). New sign-ups confirm their email before they
can add a card, connect a bank or invite people. The API and web containers run as
unprivileged accounts. Switches (`on` / `off`, empty = on in production):
`FLOWFORGE_REQUIRE_OWNER_MFA`, `FLOWFORGE_REQUIRE_VERIFIED_EMAIL`; the old open
`/auth/bootstrap` endpoint is off in production (`FLOWFORGE_ALLOW_BOOTSTRAP`).

Rotating the encryption key later: put the current key in `FLOWFORGE_CREDENTIALS_KEY_PREVIOUS`,
a new one in `FLOWFORGE_CREDENTIALS_KEY`, restart, then run
`docker compose -p flowforge -f compose.production.yml --env-file .env.production run --rm migrate python -m flowforge.accounts.reencrypt`
and remove the previous key once `--check` reports everything on the current key.

## Migrations

New schema changes are Alembic revisions under `migrations\versions`. `Start-FlowForge.ps1 -Build`
rebuilds the image and the `migrate` service applies them before the API starts.
Rehearse first with `Invoke-FlowForgeRehearsal.ps1` (disposable stack on ports 3300/8300).

Apply a new release the safe way (rehearsal from a fresh production backup, then the
update with backup, rollback-tagged images and verification):

```powershell
.\scripts\production\Invoke-FlowForgeRehearsal.ps1 -FromProductionBackup
```

```powershell
.\scripts\production\Update-FlowForge.ps1
```

## Billing (usage-based)

Pricing and costs: `docs/KROV_PRICING.md`. The API meters every workspace (activity as it
happens, storage daily), issues invoices on the 1st of each month, emails them to each
workspace's owners and charges the saved card 3 business days later (retried on the next
business day if declined, 3 tries). Your own workspace (`FLOWFORGE_BILLING_EXEMPT`,
default `flowforge-production`) is never billed. Rehearsals never bill, email or charge.

Turn on card charges and invoice email (hidden prompts; keys go to `.env.production`):

```powershell
.\scripts\production\Set-FlowForgeConnections.ps1 -Only Stripe
```

```powershell
.\scripts\production\Set-FlowForgeConnections.ps1 -Only Email
```

Start Stripe with a test key (`sk_test_...`, card 4242 4242 4242 4242) and switch to the
live key when you are ready to charge real cards. Until email is configured, invoices are
written to the API's mail outbox; read them with:

```powershell
docker exec flowforge-api-1 ls /data/mail-outbox
```

Change prices by changing costs or margin in `.env.production`
(`FLOWFORGE_COST_STORAGE_GB_MONTH`, `FLOWFORGE_COST_PER_1K_REQUESTS`,
`FLOWFORGE_TARGET_MARGIN`), run the update, and update `website/krov-config.js` to match.

## Website

The Cloudflare Pages site is in `website/` (see its README). Set `KROV_APP_URL` in
`website/krov-config.js` to the tunnel address, then upload the folder to Pages.

## Public address (Cloudflare Tunnel)

The app is branded **Krov WorkAgent** (internal names, folders and scripts keep
"flowforge"). Its web, API and database ports listen on this computer only
(127.0.0.1). Other computers reach it through Cloudflare Tunnel: the `tunnel` service
makes an outbound connection to Cloudflare, so no router ports are opened and your home
IP address stays hidden. HTTPS is provided by Cloudflare.

1. Put your domain on Cloudflare (for example `krovworkagent.com`).
2. Cloudflare dashboard → Zero Trust → Networks → Tunnels → **Create a tunnel** →
   Cloudflared → name it → copy the token (the long string after `--token`).
3. Add a **public hostname**: `app.krovworkagent.com`, service type **HTTP**, URL **web:3000**.
4. Recommended: Zero Trust → Access → Applications → add the same hostname with a policy
   that allows only your team's email addresses.
5. Run (asks for the token with hidden input, then checks the address answers):

```powershell
.\scripts\production\Set-FlowForgeTunnel.ps1
```

6. If you use Gusto, change its redirect URL to `https://<your address>/connections/payroll/callback`.

Turn the public address off again (the app stays available on this computer):

```powershell
.\scripts\production\Set-FlowForgeTunnel.ps1 -Disable
```

The site is up only while this computer is on, awake and running Docker Desktop. Set
Windows power options so it never sleeps, and copy backups off this computer regularly.
Rehearsals never start the tunnel.

## Problem reports

The in-app problem report form sends email when `FLOWFORGE_SUPPORT_SMTP_*` settings are
configured for the API. Without them (the default), or if the mail server fails, each
report is saved as a JSON file in the `flowforge_support` volume and the user is told it
was queued. List and read queued reports:

```powershell
docker exec flowforge-api-1 ls /data/support-outbox
```

```powershell
docker exec flowforge-api-1 cat /data/support-outbox/<reference>.json
```

## Connections (banks, payroll, carriers)

Stored connection credentials (bank tokens, Gusto tokens, carrier API keys) are encrypted
with AES-256-GCM. The key is `FLOWFORGE_CREDENTIALS_KEY` (32 random bytes, base64) when
set; otherwise it is derived from `FLOWFORGE_JWT_SECRET`. **Changing either key makes the
stored credentials unreadable** — users then reconnect their banks and carriers.

What works with no configuration: uploads, bank statement imports (CSV/OFX/QFX), payroll
file imports from any provider, and carrier tracking (each business enters its own
FedEx/UPS/USPS/DHL keys in Shipments → Carrier accounts).

**Set up Plaid and Gusto** (prompts for the keys with hidden input, writes them to
`.env.production`, keeps a backup copy of the file and restarts the API):

```powershell
.\scripts\production\Set-FlowForgeConnections.ps1
```

Plaid: sign up at dashboard.plaid.com, then Developers → Keys. Start with `sandbox` (test
banks; sign in with `user_good` / `pass_good`), then request production access and run the
script again with `production`. Gusto: create an application at dev.gusto.com, register the
redirect URL the script prints, start with `demo`; Gusto reviews apps before production.

The settings it writes, in `.env.production`:

| Setting | Turns on |
|---|---|
| `FLOWFORGE_PLAID_CLIENT_ID`, `FLOWFORGE_PLAID_SECRET`, `FLOWFORGE_PLAID_ENV` (`sandbox` or `production`) | **Connect a bank** (live feeds). Keys from dashboard.plaid.com; production needs Plaid's approval. |
| `FLOWFORGE_GUSTO_CLIENT_ID`, `FLOWFORGE_GUSTO_CLIENT_SECRET`, `FLOWFORGE_GUSTO_ENV` (`demo` or `production`) | Direct **Sign in to Gusto** in Payroll → Move from another provider. Register the redirect URL `<FLOWFORGE_PUBLIC_URL>/connections/payroll/callback` in the Gusto developer portal. |
| `FLOWFORGE_PUBLIC_URL` | The address users open FlowForge at (default `http://localhost:3000`). |
| `FLOWFORGE_CREDENTIALS_KEY` | A dedicated encryption key (see above). |

Permissions: `banking.read`, `banking.import` (clerks), `banking.connect` (owners and
managers); `shipping.read`, `shipping.track` (clerks), `shipping.connect`;
`payroll.migrate`; `documents.read`, `documents.upload` (clerks), `documents.manage`
(delete). Standard roles receive them automatically at API start.

## Audit trail export

Owners and anyone with `audit.read` can download every audited change as CSV from
Audit trail → **Export all changes** (`GET /api/v1/audit/export`); the page shows the latest 100.

## API paths and permissions

* Release APIs keep their paths (`/api/v1`, `/api/v2` ledger, `/api/v3` AP, `/api/v3b` AR,
  `/api/v4a` payroll, `/api/v4b` tax). Extended domain APIs are served at `/api/v2/<domain>/...`
  (they were previously reachable only at `/api/v1/api/v2/...`, which no client used).
* Every operation requires a permission except sign-in, health, problem reports and the
  static `/phase*/status` diagnostics; an operation without a policy is refused.
  `GET /api/v1/operations` lists every operation with its permission and workspace.
* Standard roles receive new permissions automatically at API start (additive only).
  Custom roles never gain permissions on their own: grant extended-domain permissions
  to them in Administration → Roles.

## Cutover history and rollback

The live system moved from the recovered runtime (database container
`forgeflow-v4-phase0-postgres-1`, API `flowforge-phase1-api-1`, web
`flowforge-phase1-web-1`) to this stack with `Invoke-FlowForgeCutover.ps1`.
The old containers and the recovered database are **stopped, not deleted**, with
restart disabled. Records are in `var\cutover\<timestamp>\`.

To return to the old runtime:

```powershell
.\scripts\production\Rollback-FlowForgeCutover.ps1
```

Keep the recovered database for about 30 days. It also archives the legacy data that
was deliberately not imported (16 automated test-run organizations, their business
rows, and 19 legacy identity users).

## What was imported

* Tenant `flowforge-production`, its user(s), roles, role permissions, user-role
  assignments and the permission catalog (IDs preserved; password hash copied).
* 57 US jurisdictions into `tax_jurisdictions` (legacy IDs kept).
* 9 payroll import providers into `integrations_provider_definitions`
  (`data.category = payroll_import`, legacy IDs in `data.legacy_source_id`).
* 19 standard units of measure (seeded by migration `ff_seed_uom_001`).
