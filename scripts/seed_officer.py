"""Create the initial super_admin officer in the secadmin schema.

Usage:
    python scripts/seed_officer.py --telegram-id 123456789 --display-name "Admin User"
"""

from __future__ import annotations

import argparse

from app.config import load_config
from app.database.secadmin_models import Officer
from app.database.session import close_db, init_secadmin_db


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed an initial super_admin officer")
    parser.add_argument("--telegram-id", type=int, required=True, help="Telegram user ID")
    parser.add_argument("--display-name", type=str, default="Admin", help="Display name")
    args = parser.parse_args()

    config = load_config()
    await init_secadmin_db(config)

    from app.database.session import get_secadmin_sessionmaker

    sm = get_secadmin_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select

        stmt = select(Officer).where(Officer.telegram_id == args.telegram_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(
                f"Officer with telegram_id={args.telegram_id} already exists (role={existing.role})"
            )
            return

        officer = Officer(
            telegram_id=args.telegram_id,
            role="super_admin",
            display_name=args.display_name,
        )
        session.add(officer)
        await session.flush()
        await session.commit()
        print(f"Created super_admin officer: id={officer.id}, telegram_id={officer.telegram_id}")

    await close_db()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
