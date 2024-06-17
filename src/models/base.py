import datetime
import uuid
from sqlmodel import Field, SQLModel as _SQLModel
from sqlalchemy.orm import declared_attr
from sqlalchemy import text


import re
from functools import partial

_snake_1 = partial(re.compile(r"(.)((?<![^A-Za-z])[A-Z][a-z]+)").sub, r"\1_\2")
_snake_2 = partial(re.compile(r"([a-z0-9])([A-Z])").sub, r"\1_\2")


def snake_case(string: str) -> str:
    return _snake_2(_snake_1(string)).casefold()


class SQLModel(_SQLModel):
    @declared_attr
    def __tablename__(cls) -> str:
        return snake_case(f"{cls.__name__}s")


class BaseSQLModel(SQLModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()"), "unique": True},
    )

    created_by: str = Field(
        nullable=False,
        sa_column_kwargs={"server_default": "admin"},
    )
    updated_by: str = Field(
        nullable=False,
        sa_column_kwargs={"server_default": "admin"},
    )
    updated_by: str = Field(
        nullable=False,
        sa_column_kwargs={"server_default": "admin"},
    )

    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        sa_column_kwargs={"server_default": text("current_timestamp(0)")},
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("current_timestamp(0)"),
            "onupdate": text("current_timestamp(0)"),
        },
    )


class Model(_SQLModel):
    pass
