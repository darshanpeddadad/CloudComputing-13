import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


async def init_db() -> None:
    """Create database tables if they do not exist."""
    from app.auth import models  # noqa: F401
    from app.interests.models import interest  # noqa: F401
    from app.events import models as event_models  # noqa: F401
    from app.tickets import models as ticket_models  # noqa: F401
    from app.rewards import models as reward_models  # noqa: F401
    from app.offers import models as offer_models  # noqa: F401
    from app.chat import models as chat_models  # noqa: F401
    from app.resale import models as resale_models  # noqa: F401
    from app.users.models import event_bookmark  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
