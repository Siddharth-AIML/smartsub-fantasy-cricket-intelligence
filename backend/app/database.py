from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.config import settings

Base = declarative_base()

# Configure Async Engine
# If using SQLite async, handle connect args
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Synchronous Engine for scripts / seed data / testing
sync_connect_args = {"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {}
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    connect_args=sync_connect_args
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
