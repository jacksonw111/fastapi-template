import base64
import datetime
import logging
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from redis import Redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import secrets

from src.extensions import Extensions
from src.libs.passport import hash_password, verify_password
from src.libs.token import access_token, refresh_token
from src.models.account import Account, AccountCreate, AccountStatus
from src.config import settings


class AccountService:
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(Extensions.db)],
        redis: Annotated[Redis, Depends(Extensions.redis)],
    ) -> None:
        self.session = session
        self.redis = redis

    async def create(self, account_create: AccountCreate) -> Account:
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        password_hashed = hash_password(password=account_create.password, salt=salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()
        account = Account(
            email=account_create.email,
            name=account_create.name,
            password=base64_password_hashed,
            role=account_create.role,
            password_salt=base64_salt,
        )
        self.session.add(account)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(account)

        return account

    async def check_account_status(self, account: Account):
        if (
            account.status == AccountStatus.BANNED.value
            or account.status == AccountStatus.CLOSED.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="account is banned or closed",
            )

    async def get_by_email(self, email: str) -> Account:
        statement = select(Account).where(Account.email == email)
        account = (await self.session.exec(statement)).one_or_none()
        return account

    async def get_account_by_email(self, email: str) -> Account:
        account = await self.get_by_email(email)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="account not found"
            )
        return account

    async def get_account_by_id(self, account_id: uuid.UUID):
        return (
            await self.session.exec(select(Account).where(Account.id == account_id))
        ).one_or_none()

    async def authenticate(self, email: str, password: str) -> Account:
        account: Account = await self.get_account_by_email(email)
        await self.check_account_status(account=account)

        if account.status == AccountStatus.PENDING:
            account.status = AccountStatus.ACTIVE.value
            account.initialized_at = datetime.datetime.now()
            self.session.add(account)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(account)

        salt = base64.b64decode(account.password_salt)
        logging.info(f"salt: {account.password_salt}")
        logging.info(f"password: {account.password}")

        if not verify_password(password, account.password, salt):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invaild account or password",
            )
        return account

    async def make_access_token(self, account: Account, tenant_id: uuid.UUID):
        token = access_token(
            account=account, tenant_id=tenant_id
        )
        await self.redis.setex(
            name=f"account:{account.id}:access_token",
            time=datetime.timedelta(days=settings.EXP_DAYS),
            value=token,
        )

        return token

    async def make_refresh_token(self, account: Account):
        token = refresh_token(account=account)
        await self.redis.setex(
            name=f"account:{account.id}:refresh_token",
            time=datetime.timedelta(days=180),
            value=token,
        )
        return token

    async def verify_refresh_token(self, account_id: str, refresh_token):
        redis_refresh_token = await self.redis.get(
            f"account:{account_id}:refresh_token"
        )
        logging.info(refresh_token)

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="invalid refresh token1"
            )

        if refresh_token != redis_refresh_token.decode("utf-8"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="invalid refresh token2"
            )

    async def remove_token(self, account_id: str):
        await self.redis.delete(f"account:${account_id}:access_token")
        await self.redis.delete(f"account:${account_id}:refresh_token")
