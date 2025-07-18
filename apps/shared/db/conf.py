import os
from sqlalchemy import URL
from dotenv import load_dotenv

load_dotenv()

# DB_USER = os.getenv("DB_USER", "postgres")
# DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
# DB_HOST = os.getenv("DB_HOST", "db")
# DB_PORT = os.getenv("DB_PORT", "5432")
# DB_NAME = os.getenv("DB_NAME", "postgres")
# DB_DRIVER = os.getenv("DB_DRIVER", "asyncpg")

# SQLALCHEMY_DATABASE_URL = (
#     f"postgresql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# )

# DATABASE_URL = URL.create(
#     drivername="postgresql+asyncpg",
#     username=DB_USER,
#     password=DB_PASSWORD,
#     host=DB_HOST,
#     port=DB_PORT,
#     database=DB_NAME,
#)
SQLALCHEMY_DATABASE_URL = (
            f"postgresql+asyncpg://"
            f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )

print(f'#SQLALCHEMY_DATABASE_URL {SQLALCHEMY_DATABASE_URL} ')