from typing import Set
from datetime import datetime
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

__all__ = ["Base", "Tag", "Autoresponse"]


class Base(DeclarativeBase):
    pass


class Tag(Base):
    __tablename__ = "tag"

    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100))
    server_id: Mapped[int] = mapped_column(index=True)
    author_id: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(String(2000))

    time_created: Mapped[datetime] = mapped_column(default=datetime.now())
    time_updated: Mapped[datetime] = mapped_column(
        default=datetime.now(), onupdate=datetime.now()
    )

    UniqueConstraint(server_id, name)

    autoresponses: Mapped[Set["Autoresponse"]] = relationship(back_populates="tag")

    def __repr__(self) -> str:
        return f"Tag(name={self.name!r}, server_id={self.server_id!r}, author_id={self.author_id!r})"


class Autoresponse(Base):
    __tablename__ = "autoresponse"

    response_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(index=True)

    phrase: Mapped[str] = mapped_column(String(4000))
    author_id: Mapped[int] = mapped_column()

    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.tag_id"))
    tag: Mapped["Tag"] = relationship(back_populates="autoresponses")

    def __repr__(self) -> str:
        return f"Autoresponse(tag={self.tag.name if self.tag else None!r}, server_id={self.server_id!r}, author_id={self.author_id!r})"
