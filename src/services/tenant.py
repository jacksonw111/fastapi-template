from typing import List
import uuid
from xmlrpc.client import boolean

from fastapi import Depends, HTTPException
from sqlalchemy import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src import extensions
from src.models.account import (
    Account,
    AccountRole,
    Tenant,
    TenantAccountJoin,
    TenantAccountJoinRole,
)


class TenantService:
    def __init__(
        self, session: AsyncSession = Depends(extensions.Extensions.db)
    ) -> None:
        self.session = session

    async def __have_edit_permission(
        self, account: Account, tenant_id: UUID
    ) -> boolean:
        if AccountRole(account.role) == AccountRole.SUPER_ADMIN:
            return True

        statement = (
            select(TenantAccountJoin)
            .where(TenantAccountJoin.account_id == account.id)
            .where(TenantAccountJoin.tenant_id == tenant_id)
        )

        tenant_join = (await self.session.exec(statement)).one_or_none()
        if tenant_join and tenant_join.role == TenantAccountJoinRole.ADMIN:
            return True

        return False

    async def create(self, account: Account, workspace: str) -> Tenant:
        if account.get_role() != AccountRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=403, detail="Only super admin can create tenant."
            )
        if (await self.session.exec(select(Tenant).where(Tenant.workspace == workspace))).first():
            raise HTTPException(status_code=400, detail="Tenant workspace already exists.")

        tenant = Tenant(owner_id=account.id, workspace=workspace)
        self.session.add(tenant)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def add_account(
        self, account: Account, tenant_id: uuid.UUID, role: TenantAccountJoinRole
    ):

        if not await self.__have_edit_permission(account=account, tenant_id=tenant_id):
            raise HTTPException(detail="no permission to edit tenant")

        if (
            await self.session.exec(
                select(TenantAccountJoin).where(
                    TenantAccountJoin.account_id == account.id
                )
            )
        ).one_or_none():
            raise HTTPException(
                detail=f"account exists in tenant. tenant_id={tenant_id}"
            )

        if not (
            await self.session.exec(select(Tenant).where(Tenant.id == tenant_id))
        ).one_or_none():
            raise HTTPException(detail=f"tenant not found. id={tenant_id}")

        if not (
            await self.session.exec(select(Account).where(Account.id == account.id))
        ).one_or_none():
            raise HTTPException(detail=f"account not found. id={account.id}")

        tenant_join = TenantAccountJoin(
            account_id=account.id, tenant_id=tenant_id, role=role
        )
        self.session.add(tenant_join)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(tenant_join)
        return tenant_join

    async def get_tenants(self, account: Account) -> List[Tenant]:
        if account.get_role() == AccountRole.SUPER_ADMIN:
            statement = select(Tenant)
            tenants = (await self.session.exec(statement)).all()
        else:
            statement = select(TenantAccountJoin, Tenant).where(
                TenantAccountJoin.account_id == account.id,
                Tenant.id == TenantAccountJoin.tenant_id,
            )
            all_joins = (await self.session.exec(statement)).all()
            tenants = [tenant for _, tenant in all_joins]

        return tenants
