from dotenv import load_dotenv, find_dotenv
from sqlalchemy.orm import sessionmaker
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

load_dotenv(find_dotenv(filename="my_dotenv.env.dev"))

user = os.getenv("POSTGRES_USER")
passw = os.getenv("POSTGRES_PASSWORD")
db = os.getenv("POSTGRES_DB")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{user}:{passw}@{host}:{port}/{db}"
database_engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = AsyncSession(
    autocommit=False, autoflush=False, bind=database_engine
)
