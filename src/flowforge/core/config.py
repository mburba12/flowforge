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
    # Largest uploaded file, in bytes.
    upload_max_bytes: int = 20 * 1024 * 1024


settings = Settings()
