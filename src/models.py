from typing import Set
from datetime import datetime
import re

from sqlalchemy import String
from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

__all__ = ["Base", "Tag", "Autoresponse"]

import sqlalchemy.types as types

class Regex(types.TypeDecorator):
    '''Prefixes Unicode values with "PREFIX:" on the way in and
    strips it off on the way out.
    '''

    impl = types.String

    cache_ok = True

    def process_bind_param(self, value: str, dialect) -> re.Pattern:
        return re.compile(pattern=value)

    def process_result_value(self, value: re.Pattern, dialect) -> str:
        return value.pattern

    def copy(self, **kw):
        return Regex(self.impl.length) # type: ignore

class Base(DeclarativeBase):
    pass


class Tag(Base):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String(100))
    server_id: Mapped[int] = mapped_column(index=True)
    author_id: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(String(2000))

    time_created: Mapped[datetime] = mapped_column(default=datetime.now())
    time_updated: Mapped[datetime] = mapped_column(
        default=datetime.now(), onupdate=datetime.now()
    )

    UniqueConstraint(server_id, name)
    PrimaryKeyConstraint(server_id, name)

    autoresponses: Mapped[Set["Autoresponse"]] = relationship(back_populates="tag")

    def __repr__(self) -> str:
        return f"Tag(name={self.name!r}, server_id={self.server_id!r}, author_id={self.author_id!r})"


class Autoresponse(Base):
    __tablename__ = "autoresponse"

    response_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("tag.server_id"), index=True)

    regex: Mapped[re.Pattern] = mapped_column(Regex(4000))
    author_id: Mapped[int] = mapped_column()

    tag_name: Mapped[str] = mapped_column(ForeignKey("tag.name"))
    tag: Mapped["Tag"] = relationship(back_populates="autoresponses")

    def __repr__(self) -> str:
        return f"Autoresponse(tag={self.tag.name if self.tag else None!r}, server_id={self.server_id!r}, author_id={self.author_id!r})"
