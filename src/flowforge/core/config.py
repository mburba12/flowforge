from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FLOWFORGE_")
    env: str = "development"
    database_url: str = "postgresql+asyncpg://flowforge:flowforge@localhost:5433/flowforge"
    jwt_secret: str = "development-only-change-me-32-characters"
    access_token_minutes: int = 30


settings = Settings()
