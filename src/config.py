from typing import Any, Dict, Optional
from pydantic import EmailStr, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    # default admin
    NAME: str = "newai"
    EMAIL: EmailStr = "jacksonwen001@gmail.com"
    PASSWORD: str = "newai!123"
    EXP_DAYS: int = 30
    ISS: str = "newai"
    SUB: str = "Console API Passport"

    # to get a string like this run:
    # openssl rand -hex 32
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    GEMINI_API_KEY: str = ""
    # POSTGRES
    POSTGRES_SERVER: str = "localhost:5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "Test!123"
    POSTGRES_DB: str = "screenflow"
    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    SQLALCHEMY_POOL_SIZE: int = 50
    SQLALCHEMY_POOL_PRE_PING: bool = False
    SQLALCHEMY_POOL_RECYCLE: int = 300
    SQLALCHEMY_ECHO: bool = False

    @model_validator("ASYNC_SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_async_db_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )

    # REDIS
    REDIS_SERVER: str = "localhost:6379"
    REDIS_PASSWORD: str = "Test!123"
    REDIS_DB: int = 0
    REDIS_URI: Optional[RedisDsn] = None

    @model_validator("REDIS_URI", mode="before")
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_SERVER"),
            path=f"{values.get('REDIS_DB') or ''}",
        )


settings = Setting()
