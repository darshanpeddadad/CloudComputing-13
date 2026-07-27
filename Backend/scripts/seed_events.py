import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.auth.security.auth_security import AuthSecurity
from app.database import SessionLocal, init_db
from app.seeders.auth_seed import seed_roles_and_admin
from app.seeders.event_seed import seed_event_users_and_events
from app.seeders.event_user_seed import seed_event_users
from app.auth.models import Role
from sqlalchemy import select, text


async def main() -> None:
    load_dotenv(project_root / ".env")
    await init_db()
    auth_security = AuthSecurity()
    async with SessionLocal() as session:
        await seed_roles_and_admin(session, auth_security)
        user_role = await session.scalar(select(Role).where(Role.name == "user"))
        if not user_role:
            print("Seed aborted: 'user' role not found. Run auth seeder first.")
            return
        organizers = await seed_event_users(session, auth_security, user_role)
        await session.commit()
        print(f"Ensured {len(organizers)} organizer users with 'user' role.")

        result = await session.execute(text("SELECT COUNT(*) FROM events"))
        existing_count = result.scalar() or 0
        outcome, reason = await seed_event_users_and_events(session, organizers)
        if outcome:
            organizers, categories, events = outcome
            print(f"Seeded {categories} categories, {organizers} organizers, {events} events.")
        else:
            if reason == "events_exist":
                print(f"Seed skipped: {existing_count} events already exist for {session.bind.url}.")
            elif reason == "no_organizers":
                print("Seed skipped: no organizer users available.")
            else:
                print("Seed skipped: unknown reason.")


if __name__ == "__main__":
    asyncio.run(main())
