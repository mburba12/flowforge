from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FLOWFORGE_")
    env: str = "development"
    database_url: str = "postgresql+asyncpg://flowforge:flowforge@localhost:5433/flowforge"
    jwt_secret: str = "development-only-change-me-32-characters"
    access_token_minutes: int = 30
    # Encrypts stored connection credentials (bank, payroll and carrier tokens).
    # 32 random bytes, base64. When unset a key is derived from jwt_secret.
    credentials_key: str = ""
    # Older keys still accepted for reading (comma-separated, base64) during rotation.
    credentials_key_previous: str = ""
    # Public address of the web app (OAuth redirects come back here).
    public_url: str = "http://localhost:3000"
    # Bank connections through Plaid (https://dashboard.plaid.com): sandbox or production.
    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"
    # Payroll migration from Gusto (https://dev.gusto.com): demo or production.
    gusto_client_id: str = ""
    gusto_client_secret: str = ""
    gusto_env: str = "demo"
    # Account security switches: "on", "off", or "" (= production default, see accounts.policy).
    require_owner_mfa: str = ""
    require_verified_email: str = ""
    allow_bootstrap: str = ""
    # Cloudflare Turnstile (bot check on sign-up and password reset); off when empty.
    turnstile_site_key: str = ""
    turnstile_secret: str = ""
    # Limits on public sign-in / sign-up attempts: "on", "off", or "" (= on in production).
    rate_limits: str = ""
    # --- Usage billing (docs/KROV_PRICING.md) ---------------------------------------
    # "on", "off", or "" (= on in production). Rehearsals and tests turn it off.
    billing: str = ""
    # Workspaces never billed (comma-separated slugs): your own business.
    billing_exempt: str = "flowforge-production"
    # What one unit costs you (USD); prices = (cost + card fixed fee) / (1 - margin - card %).
    cost_storage_gb_month: float = 2.00
    cost_per_1k_requests: float = 0.0245
    cost_bank_connection_month: float = 0.25
    bill_bank_connections: bool = False  # data sync is free: bank feeds are not charged
    target_margin: float = 0.70
    card_fee_percent: float = 0.029
    card_fee_fixed: float = 0.30
    billing_currency: str = "usd"
    # Stripe (dashboard.stripe.com -> Developers -> API keys): secret key sk_test_/sk_live_.
    stripe_secret_key: str = ""
    # Outgoing email for invoices (any SMTP service: Postmark, SES, Microsoft 365...).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    mail_from: str = ""
    mail_outbox: str = "var/mail-outbox"
    # Largest uploaded file, in bytes.
    upload_max_bytes: int = 20 * 1024 * 1024


settings = Settings()
