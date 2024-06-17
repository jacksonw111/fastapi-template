from typing import Any, Dict, Optional
from pydantic import EmailStr, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    # default admin
    NAME: str
    EMAIL: EmailStr
    PASSWORD: str
    EXP_DAYS: int
    ISS: str
    SUB: str

    # to get a string like this run:
    # openssl rand -hex 32
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_DAYS: int

    # POSTGRES
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
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
    REDIS_SERVER: str
    REDIS_PASSWORD: str
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
