from typing import List, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Role, User

SEED_USER_COUNT = 10
SEED_USERS: Sequence[dict[str, str]] = (
    {
        "email": "event-user-01@seed.fulda",
        "first_names": "Taylor",
        "last_name": "Morgan",
        "dob": "1993-01-15",
    },
    {
        "email": "event-user-02@seed.fulda",
        "first_names": "Jordan",
        "last_name": "Blake",
        "dob": "1990-05-22",
    },
    {
        "email": "event-user-03@seed.fulda",
        "first_names": "Riley",
        "last_name": "Bennett",
        "dob": "1994-08-03",
    },
    {
        "email": "event-user-04@seed.fulda",
        "first_names": "Skylar",
        "last_name": "Hayes",
        "dob": "1991-11-17",
    },
    {
        "email": "event-user-05@seed.fulda",
        "first_names": "Cameron",
        "last_name": "Ellis",
        "dob": "1989-02-09",
    },
    {
        "email": "event-user-06@seed.fulda",
        "first_names": "Alexis",
        "last_name": "Reed",
        "dob": "1992-07-26",
    },
    {
        "email": "event-user-07@seed.fulda",
        "first_names": "Morgan",
        "last_name": "Lee",
        "dob": "1995-03-30",
    },
    {
        "email": "event-user-08@seed.fulda",
        "first_names": "Reese",
        "last_name": "Coleman",
        "dob": "1996-12-05",
    },
    {
        "email": "event-user-09@seed.fulda",
        "first_names": "Peyton",
        "last_name": "Wells",
        "dob": "1993-09-14",
    },
    {
        "email": "event-user-10@seed.fulda",
        "first_names": "Casey",
        "last_name": "Flynn",
        "dob": "1994-04-21",
    },
)


async def seed_event_users(
    session: AsyncSession,
    security,
    user_role: Role,
    target_count: int = SEED_USER_COUNT,
) -> List[User]:
    if target_count > len(SEED_USERS):
        raise ValueError("target_count exceeds available seed user profiles")

    seed_specs = list(SEED_USERS[:target_count])
    stmt = (
        select(User)
        .where(User.email.like("event-user-%@seed.fulda"))
        .options(selectinload(User.roles))
    )
    existing_users = list(await session.scalars(stmt))
    existing_by_email = {user.email: user for user in existing_users}
    seeded_users: List[User] = []

    for spec in seed_specs:
        email = spec["email"]
        user = existing_by_email.get(email)
        if not user:
            user = User(
                id=security.generate_user_id(),
                first_names=spec["first_names"],
                last_name=spec["last_name"],
                email=email,
                dob=spec["dob"],
                password_hash=security.hash_password("SeedUser!1"),
            )
            user.roles = [user_role]
            session.add(user)
        else:
            user.first_names = spec["first_names"]
            user.last_name = spec["last_name"]
            user.dob = spec["dob"]
            if not any(role.id == user_role.id for role in user.roles):
                user.roles.append(user_role)
        seeded_users.append(user)

    await session.flush()
    return seeded_users
