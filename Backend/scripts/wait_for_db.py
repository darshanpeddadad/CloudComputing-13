import asyncio
import os

import asyncmy
from sqlalchemy.engine import make_url

MAX_ATTEMPTS = 30
SLEEP_SECONDS = 2


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    url = make_url(database_url)
    host = url.host or "localhost"
    port = url.port or 3306
    user = url.username or "root"
    password = url.password or ""
    database = url.database or ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            conn = await asyncmy.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                db=database,
                connect_timeout=5,
            )
            await conn.ensure_closed()
            print(f"Database connection established on attempt {attempt}.")
            return
        except Exception as exc:
            print(f"Database not ready (attempt {attempt}/{MAX_ATTEMPTS}): {exc}")
            await asyncio.sleep(SLEEP_SECONDS)
    raise RuntimeError("Database never became available")


if __name__ == "__main__":
    asyncio.run(main())
