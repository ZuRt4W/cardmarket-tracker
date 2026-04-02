from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cm_app_token: str
    cm_app_secret: str
    cm_access_token: str
    cm_access_token_secret: str
    database_url: str
    collect_hour: int = 8
    collect_minute: int = 0
    max_retries: int = 3
    retry_backoff: float = 2.0

    class Config:
        env_file = ".env"


settings = Settings()
