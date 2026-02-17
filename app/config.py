from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://user:password@postgres:5432/userdb"
    mailhog_smtp_host: str = "mailhog"
    mailhog_smtp_port: int = 1025
    mailhog_api_url: str = "http://mailhog:8025"


settings = Settings()
