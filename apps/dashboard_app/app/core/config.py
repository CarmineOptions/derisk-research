
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