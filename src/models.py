
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class Base(DeclarativeBase):
    pass

class Tag(Base):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    server_id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(String(2000))

    def __repr__(self) -> str:
        return f"Tag(name={self.name!r}, server_id={self.server_id!r}, author_id={self.author_id!r})"