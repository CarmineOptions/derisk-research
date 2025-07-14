from typing import Any
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    db_driver: str = "postgresql+asyncpg"
    db_name: str = Field(default="db_name", alias="POSTGRES_DB")
    db_user: str = Field(default="user", alias="POSTGRES_USER")
    db_password: str = Field(default="password", alias="POSTGRES_PASSWORD")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = 5432

    derisk_api_url: str = Field(default="http://derisk-api.com", env="DERISK_API_URL")
    network: str = Field(default="sepolia", alias="NETWORK")
    active_protocols: list = Field(
        default_factory=lambda: ["ZkLend", "NostraMainnet", "NostraAlpha"],
        alias="ACTIVE_PROTOCOLS",
    )

    coingecko_api_key: str = "api_key"
    coingecko_api_url: str = "api_url"

    @property
    def _required_fields(self) -> dict[str, Any]:
        """Returns a dictionary with required fields for database_url.
        Fields that have an alias have an alias key."""
        return {
            "db_driver": self.db_driver,
            "db_port": self.db_port,
            "POSTGRES_USER": self.db_user,
            "POSTGRES_PASSWORD": self.db_password,
            "DB_HOST": self.db_host,
            "POSTGRES_DB": self.db_name,
        }

    @property
    def database_url(self) -> str:
        """Generate a full PostgreSQL database connection URL
        based on config settings.
        Returns:
        str: postgresql+asyncpg://<user>:<password>@<host>:<port>/<db_name>"""

        for alias, value in self._required_fields.items():
            if value in (None, ""):
                raise ValueError(f"Missing required environment variable: {alias}")
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
