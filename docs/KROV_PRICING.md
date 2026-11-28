# Krov WorkAgent: cloud costs and usage pricing

Every feature is included for every customer. Customers pay only for what they use:
**storage** (their records and files) and **activity** (actions in the app). Moving data
in (payroll, bank statement and shipment imports) and keeping it in sync (bank feeds,
tracking refresh, Gusto) are free. Each customer's bill is therefore different.

## 1. What running it in the cloud costs you (per month)

A launch-size setup that serves roughly 50–150 small businesses. Prices are list prices
found in November 2026; confirm them on each provider's pricing page before you sign up.

| Item | Choice | Monthly |
|---|---|---|
| App server | DigitalOcean Droplet, 4 vCPU / 8 GB | $48.00 |
| Database | DigitalOcean Managed PostgreSQL (about 4 GB RAM, ~30 GB used) | ~$60.00 |
| Server backups | Droplet weekly backups (20% of the droplet) | $9.60 |
| Invoice and notice email | Postmark, 10,000 emails | $15.00 |
| Public address, HTTPS, protection | Cloudflare Tunnel and DNS (free plan) | $0.00 |
| Domain name | about $12 a year | ~$1.00 |
| **Fixed total** | | **~$133.60** |

Costs per customer and per payment:

| Item | Cost |
|---|---|
| Card payments (Stripe, US cards) | 2.9% + $0.30 per monthly charge |
| Live bank feeds (Plaid, per connected account) | roughly $0.25+ per account per month; quote from Plaid sales. Not charged to customers, because data sync is free. Switch `FLOWFORGE_BILL_BANK_CONNECTIONS=true` to pass it on. |
| Gusto, FedEx, UPS, USPS, DHL APIs | $0 (customers use their own carrier accounts) |

While it runs on your own computer through the tunnel, the cloud servers cost nothing;
only Stripe, email and Plaid apply.

## 2. Cost of one unit (what the app meters)

| Unit | How it is measured | Your cost | How the cost is worked out |
|---|---|---|---|
| Storage, per GB-month | every workspace's rows and files, measured daily, averaged over the month | **$2.00** | database $60 ÷ ~30 GB of usable space |
| Activity, per 1,000 actions | every signed-in request, except sign-in, imports and sync | **$0.0245** | server + backups + email + domain ($73.60) ÷ ~3,000,000 actions the server handles comfortably |
| Card processing, per invoice | one charge per month | **$0.30 + 2.9%** | Stripe |

A person working in the app all day makes roughly 200–400 actions (each screen loads a few).

## 3. The price formula (70% margin on every invoice)

```
price = (usage cost + $0.30) ÷ (1 − 0.70 − 0.029)
      = (usage cost + $0.30) ÷ 0.271
```

After Stripe takes 2.9% + $0.30, exactly 70% of every invoice is left over as profit. The
customer sees these unit prices:

| | Customer price |
|---|---|
| Storage | **$7.38 per GB per month** |
| Activity | **$0.09 per 1,000 actions** |
| Card processing | **$1.11 per monthly payment** |
| Every feature, data migration, bank / payroll / carrier sync | **Included, $0** |

## 4. What customers would pay (calculated by the app's own billing code)

| Customer | Storage | Actions / month | Bill | Your cost | Card fee | Profit | Margin |
|---|---|---|---|---|---|---|---|
| Solo / very light | 0.1 GB | 8,000 | **$2.57** | $0.40 | $0.37 | $1.80 | 70% |
| Small business (3–5 people) | 0.5 GB | 60,000 | **$10.22** | $2.47 | $0.60 | $7.15 | 70% |
| Growing business | 2 GB | 250,000 | **$38.47** | $10.13 | $1.42 | $26.93 | 70% |
| Busy company | 10 GB | 1,200,000 | **$183.40** | $49.40 | $5.62 | $128.38 | 70% |
| Large company | 40 GB | 5,000,000 | **$748.34** | $202.50 | $22.00 | $523.84 | 70% |

## 5. Things to know before launch

* **Bills are much lower than the old plans.** The old Starter and Business plans were
  $199 and $499 a month. At cost plus 70%, a typical small business pays about $10 a
  month. The margin is 70%, but the dollars per customer are small, so revenue depends on
  having many customers.
* **The 70% assumes the servers are used.** Unit costs assume the database holds about
  30 GB and the server handles about 3 million actions a month. Until customers use that
  much, part of the fixed $133.60 is not covered. Break-even on the fixed cost alone is
  roughly $490 a month in total bills (about 50 small businesses). When usage grows past
  the plan, a larger server raises cost and capacity together, so the unit costs stay
  about the same.
* **Changing a rate:** the settings are in `.env.production` (`FLOWFORGE_COST_STORAGE_GB_MONTH`,
  `FLOWFORGE_COST_PER_1K_REQUESTS`, `FLOWFORGE_TARGET_MARGIN`). Customer prices follow
  automatically. Update the website calculator (`krov-config.js`) to match.
* **Your own workspace** (`flowforge-production`) is never billed (`FLOWFORGE_BILLING_EXEMPT`).
* **Cheaper file storage later:** uploaded files are stored in the database today, at $2.00
  per GB. Moving files to Cloudflare R2 ($0.015 per GB-month, no download fees) would make
  file-heavy customers much cheaper. That is a future change.

## 6. How billing runs

1. Usage is recorded all month: activity as it happens, storage once a day.
2. On the **1st of each month**, every customer gets an invoice for the month before. It
   is emailed to the workspace's owners and lists storage, activity and card processing.
   It says which card will be charged, the amount, and the date: **3 business days after
   the invoice** (weekends and US bank holidays skipped).
3. On that date the saved card is **charged automatically**. If it is declined, the owners
   get an email and the charge is retried the next business day (3 tries in total). After
   that, the owner can pay from Billing & usage.
4. Customers add a card in **Billing & usage**. They first tick that they authorize
   automatic monthly charges, then type the card on Stripe's secure page. Krov WorkAgent
   only ever stores Stripe's reference, the brand, the last 4 digits and the expiry.

Turn it on: run `.\scripts\production\Set-FlowForgeConnections.ps1 -Only Stripe` and
`-Only Email`. Until email is set up, invoices are saved in the API's mail outbox
(`/data/mail-outbox`). Until Stripe is set up, invoices stay open and are not charged.

Sources: [DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets),
[DigitalOcean managed database pricing](https://www.digitalocean.com/pricing/managed-databases),
[Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/),
[Stripe fees overview](https://checkoutpage.com/blog/stripe-processing-fees),
[Postmark pricing](https://postmarkapp.com/pricing),
[Plaid billing](https://plaid.com/docs/account/billing/).
