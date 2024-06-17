import logging
from fastapi import APIRouter, Depends, HTTPException, status

from src.models.account import AccountCreate, AccountRole, Tenant, TenantAccountJoinRole
from src.services.account import AccountService
from src.services.tenant import TenantService
from src.config import settings

api = APIRouter()


@api.get("/setup")
async def create(
    account_service: AccountService = Depends(AccountService),
    tenant_service: TenantService = Depends(TenantService),
):
    account = await account_service.get_by_email(settings.EMAIL)
    if account:
        return

    try:
        account = await account_service.create(
            AccountCreate(
                name=settings.NAME,
                email=settings.EMAIL,
                password=settings.PASSWORD,
                role=AccountRole.SUPER_ADMIN,
            )
        )

        tenant: Tenant = await tenant_service.create(
            account, f"{settings.NAME}'s workspace"
        )

        await tenant_service.add_account(
            account,
            tenant.id,
            TenantAccountJoinRole.ADMIN,
        )

    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {
        "name": settings.NAME,
        "email": settings.EMAIL,
        "password": settings.PASSWORD,
        "workspace": tenant.workspace,
    }
