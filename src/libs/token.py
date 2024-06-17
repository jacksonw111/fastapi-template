import datetime
import uuid

import jwt
from src.models.account import Account
from src.config import settings


def make_token(
    account: Account,
    tenant_id: uuid.UUID = None,
    expire_day: int = settings.EXP_DAYS,
    iss: str = settings.ISS,
    sub: str = settings.SUB,
):
    paylaod = {
        "account_id": str(account.id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "exp": datetime.datetime.now() + datetime.timedelta(days=expire_day),
        "iss": iss,
        "sub": sub,
    }

    return jwt.encode(payload=paylaod, key=settings.SECRET_KEY, algorithm="HS256")


def get_decoded_token(token: str):
    return jwt.decode(token, key=settings.SECRET_KEY, algorithms=["HS256"])


def access_token(account: Account, tenant_id: str):
    return make_token(
        account=account, expire_day=30, tenant_id=tenant_id, sub="access token"
    )


def refresh_token(account: Account):
    return make_token(account=account, expire_day=180, sub="refresh token")
