from functools import cached_property
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from dill import settings


class Settings(BaseSettings):
    # Database settings
    db_driver: str = "postgresql+asyncpg"
    db_name: str = Field(default="db_name", alias="POSTGRES_DB")
    db_user: str = Field(default="user", alias="POSTGRES_USER")
    db_password: str = Field(default="password", alias="POSTGRES_PASSWORD")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = 5432

    derisk_api_url: str = Field(..., env="DERISK_API_URL")
    network: str = Field(default="sepolia", alias="NETWORK")
    active_protocols: list = Field(default_factory=lambda: ["ZkLend", "NostraMainnet", "NostraAlpha"], alias="ACTIVE_PROTOCOLS")

    coingecko_api_key: str = "api_key"
    coingecko_api_url: str = "api_url"

    @cached_property
    def database_url(self) -> str:
        """Generate a full PostgreSQL database connection URL
        based on config settings.
        Returns:
        str: postgresql+asyncpg://<user>:<password>@<host>:<port>/<db_name>"""
        required_fields = [
            self.db_driver,
            self.db_user,
            self.db_password,
            self.db_host,
            self.db_port,
            self.db_name
        ]
        if any(field in (None, "") for field in required_fields):
            raise ValueError("Missing required database configuration fields.")
        return (f"{self.db_driver}://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}")


if __name__ == "__main__":
    settings = Settings()

