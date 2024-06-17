import logging
import time
import uuid
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import jwt
from redis import Redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src import extensions
from src.config import settings
from src.extensions import Extensions
from src.models.account import Account
from src.web.setup import api as setup_api_router
from src.web.auth import api as auth_api_router


app = FastAPI(openapi_url=None)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(message)s")


@app.exception_handler(RequestValidationError)
async def request_validate_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        content=jsonable_encoder({"detail": exc}),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.middleware("http")
async def add_exc_time(request: Request, call_next):
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def account_validate_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path.endswith(
        (
            "/setup",
            "/access-token",
            "/refresh-token",
            "/docs",
            "/openapi.json",
        )
    ):
        return await call_next(request)

    session = None
    redis = None

    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Expected 'Bearer <api-key>' format.",
            )
        if " " not in auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Expected 'Bearer <api-key>' format.",
            )

        auth_scheme, auth_token = auth_header.split(None, 1)
        auth_scheme = auth_scheme.lower()
        if auth_scheme != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format. Expected 'Bearer <api-key>' format.",
            )

        decoded_token = jwt.decode(
            auth_token, key=settings.SECRET_KEY, algorithms=["HS256"]
        )

        account_id = decoded_token.get("account_id")
        tenant_id = decoded_token.get("tenant_id")

        if account_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization token.",
            )

        # load account
        account_id = uuid.UUID(account_id)
        session: AsyncSession = await anext(extensions.Extensions.db(False))
        account = (
            await session.exec(select(Account).where(Account.id == account_id))
        ).one_or_none()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="the account not exists",
            )

        # redis manage session
        redis: Redis = await anext(Extensions.redis(False))
        access_token = await redis.get(
            f"account:{account_id}:access_token",
        )
        if not access_token or access_token.decode("utf-8") != auth_token:
            logging.error(f"access_token: {str(access_token) }, auth: {auth_token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization token",
            )

        request.state.account = account
        request.state.tenant_id = tenant_id
        return await call_next(request)

    except Exception as e:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content=str(e))
    finally:
        if redis:
            await redis.close()
        if session:
            await session.close()


app.include_router(setup_api_router, tags=["setup"])
app.include_router(auth_api_router, tags=["auth"])
