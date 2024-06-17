import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis import Redis

from src import extensions
from src.libs.token import get_decoded_token
from src.models.base import Model
from src.services.account import AccountService
from src.services.tenant import TenantService

api = APIRouter()


class AuthData(Model):
    email: str
    password: str


@api.post("/access-token")
async def auth(
    account_service: Annotated[AccountService, Depends()],
    tenant_service: Annotated[TenantService, Depends()],
    redis: Annotated[Redis, Depends(extensions.Extensions.redis)],
    data: AuthData,
):
    account = await account_service.authenticate(
        email=data.email, password=data.password
    )
    tenants = await tenant_service.get_tenants(account=account)
    tenant_id = tenants[0].id if tenants else None
    access_token = await account_service.make_access_token(
        account=account, tenant_id=tenant_id
    )
    refresh_token = await account_service.make_refresh_token(account=account)

    return {"access_token": access_token, "refresh_token": refresh_token}


@api.delete("/logout")
async def logout(
    request: Request, account_service: Annotated[AccountService, Depends()]
):
    await account_service.remove_token(request.state.account.id)


class RefreshToken(Model):
    access_token: str
    refresh_token: str


@api.post("/refresh-token")
async def refresh(
    account_service: Annotated[AccountService, Depends()],
    tenant_service: Annotated[TenantService, Depends()],
    token: RefreshToken,
):
    decoded_token = get_decoded_token(token=token.refresh_token)
    account_id = decoded_token.get("account_id")
    logging.info(account_id)

    await account_service.verify_refresh_token(
        account_id=account_id, refresh_token=token.refresh_token
    )

    account = await account_service.get_account_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid account3"
        )

    await account_service.check_account_status(account=account)

    tenants = await tenant_service.get_tenants(account=account)
    tenant_id = tenants[0].id if tenants else None

    await account_service.remove_token(account_id)

    access_token = await account_service.make_access_token(
        account=account, tenant_id=tenant_id
    )

    refresh_token = await account_service.make_refresh_token(account=account)

    return {"access_token": access_token, "refresh_token": refresh_token}
