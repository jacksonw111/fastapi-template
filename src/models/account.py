from datetime import datetime
import enum
from typing import Optional
import uuid
from pydantic import EmailStr, IPvAnyAddress
from sqlmodel import AutoString, Field, text

from src.models.base import BaseSQLModel, Model


class AccountStatus(str, enum.Enum):
    PENDING = "pending"
    UNINITIALIZED = "uninitialized"
    ACTIVE = "active"
    BANNED = "banned"
    CLOSED = "closed"


class AccountRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    USER = "user"


class AccountCreate(Model):
    name: Optional[str] = None
    email: EmailStr
    password: str
    role: AccountRole = AccountRole.USER


class Account(BaseSQLModel, table=True):
    name: Optional[str] = None
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    password: str
    password_salt: str
    role: str = Field(
        default="user",
        nullable=True,
        sa_column_kwargs={"server_default": text("'user'::character varying")},
    )
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[IPvAnyAddress] = Field(default=None, sa_type=AutoString)
    last_active_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("current_timestamp(0)"),
        },
    )
    status: str = Field(
        default="active",
        nullable=False,
        sa_column_kwargs={"server_default": text("'active'::character varying")},
    )
    initialized_at: Optional[datetime] = None
    space_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()"), "unique": True},
    )

    def get_status(self) -> AccountStatus:
        status_str = self.status
        return AccountStatus(status_str)

    def get_role(self) -> AccountRole:
        return AccountRole(self.role)


class TenantCreate(Model):
    owner_id: uuid.UUID
    workspace: str


class Tenant(BaseSQLModel, table=True):
    owner_id: uuid.UUID
    workspace: str


class TenantAccountJoinRole(str, enum.Enum):
    ADMIN = "admin"
    NORMAL = "normal"
    GUEST = "guest"


class TenantAccountJoin(BaseSQLModel, table=True):
    tenant_id: uuid.UUID
    account_id: uuid.UUID
    role: TenantAccountJoinRole
