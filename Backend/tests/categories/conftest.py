import asyncio
from typing import Callable, Dict

import pytest

from app.database import SessionLocal
from tests.events.utils import create_category, truncate_event_tables


@pytest.fixture(autouse=True)
def clean_categories_tables():
    """Truncate category-related tables before and after every test in this package."""
    async def _cleanup():
        async with SessionLocal() as session:
            await truncate_event_tables(session)
            await session.commit()

    asyncio.run(_cleanup())
    yield
    asyncio.run(_cleanup())


@pytest.fixture()
def category_factory() -> Callable[..., Dict]:
    """Factory fixture that synchronously creates categories for tests."""
    def _create_category(name: str = "Technology"):
        async def _run():
            async with SessionLocal() as session:
                category = await create_category(session, name)
                await session.commit()
                return category

        return asyncio.run(_run())

    return _create_category
