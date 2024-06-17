from fastapi import Query
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession as _AsyncSession

from src.config import settings


def init():
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": settings.SQLALCHEMY_POOL_SIZE,
        "pool_pre_ping": settings.SQLALCHEMY_POOL_PRE_PING,
        "pool_recycle": settings.SQLALCHEMY_POOL_RECYCLE,
        "echo": settings.SQLALCHEMY_ECHO,
    }
    async_engine = create_async_engine(
        str(settings.ASYNC_SQLALCHEMY_DATABASE_URI), **SQLALCHEMY_ENGINE_OPTIONS
    )

    AsyncSession = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=async_engine,
        class_=_AsyncSession,
        expire_on_commit=False,
    )

    async def get_async_db(
        auto_close: bool = Query(default=True, include_in_schema=False)
    ):
        try:
            db = AsyncSession()
            yield db
        finally:
            if auto_close:
                await db.close()

    return get_async_db
