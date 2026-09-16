from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
    "postgresql+asyncpg://"
    "kitchenos:REDACTED_PASSWORD@127.0.0.1:15432/kitchenos"
)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()