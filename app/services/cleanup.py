import asyncio
import logging

from app.database.repositories.deletion_logs import DeletionLogRepository
from app.database.repositories.activity import ActivityRepository
from app.database.session import get_secadmin_sessionmaker, get_session

logger = logging.getLogger(__name__)


async def periodic_log_cleanup(interval_minutes: int = 30) -> None:
    while True:
        try:
            async with get_session() as session:
                repo = DeletionLogRepository(session)
                deleted = await repo.delete_expired()
                if deleted > 0:
                    logger.info("Cleaned up %d expired deletion logs", deleted)
            try:
                sm = get_secadmin_sessionmaker()
                async with sm() as session:
                    activity_repo = ActivityRepository(session)
                    stats = await activity_repo.apply_retention()
                    await session.commit()
                    if stats["redacted_text"] or stats["deleted_metadata"]:
                        logger.info(
                            "Applied activity retention: redacted_text=%d deleted_metadata=%d",
                            stats["redacted_text"],
                            stats["deleted_metadata"],
                        )
            except RuntimeError:
                pass
        except Exception as e:
            logger.error("Error during log cleanup: %s", e)

        await asyncio.sleep(interval_minutes * 60)


def start_cleanup_task(interval_minutes: int = 30) -> asyncio.Task:
    return asyncio.create_task(periodic_log_cleanup(interval_minutes))
