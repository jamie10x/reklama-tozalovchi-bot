import asyncio
import logging

from app.database.repositories.deletion_logs import DeletionLogRepository
from app.database.session import get_session

logger = logging.getLogger(__name__)


async def periodic_log_cleanup(interval_minutes: int = 30) -> None:
    while True:
        try:
            async with get_session() as session:
                repo = DeletionLogRepository(session)
                deleted = await repo.delete_expired()
                if deleted > 0:
                    logger.info("Cleaned up %d expired deletion logs", deleted)
        except Exception as e:
            logger.error("Error during log cleanup: %s", e)

        await asyncio.sleep(interval_minutes * 60)


def start_cleanup_task(interval_minutes: int = 30) -> asyncio.Task:
    return asyncio.create_task(periodic_log_cleanup(interval_minutes))
