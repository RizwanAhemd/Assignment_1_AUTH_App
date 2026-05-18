from typing import Optional
from pydantic import PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CORE-AUTH"

    # Database Settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None

    # Redis Settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_URL: Optional[str] = None

    # JWT Settings
    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    @model_validator(mode="after")
    def assemble_connections(self) -> "Settings":
        """
        Runs AFTER individual fields are validated.
        Guarantees that host, port, user, and password strings are fully populated.
        """
        # Assemble PostgreSQL URL if not explicitly provided in .env
        if not self.DATABASE_URL:
            self.DATABASE_URL = str(
                PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=self.POSTGRES_USER,
                    password=self.POSTGRES_PASSWORD,
                    host=self.POSTGRES_SERVER,
                    port=self.POSTGRES_PORT,
                    path=self.POSTGRES_DB,
                )
            )

        # Assemble Redis URL if not explicitly provided in .env
        if not self.REDIS_URL:
            self.REDIS_URL = str(
                RedisDsn.build(
                    scheme="redis",
                    host=self.REDIS_HOST,
                    port=self.REDIS_PORT,
                    path=f"{self.REDIS_DB}",
                )
            )

        return self


settings = Settings()
