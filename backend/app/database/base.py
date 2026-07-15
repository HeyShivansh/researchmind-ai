from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 declarative base class.

    All ORM models should inherit from this class.

    Example:
        class Document(Base):
            __tablename__ = "documents"
            id: Mapped[int] = mapped_column(primary_key=True)
            ...
    """

    pass
