from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from api.schemas.dashboard import DashboardResponse
from app.database.models import Chat
from app.database.repositories.events import SecurityEventRepository
from app.database.repositories.outbox import OutboxRepository
from app.database.secadmin_models import Indicator, Officer

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    event_repo = SecurityEventRepository(session)
    outbox_repo = OutboxRepository(session)

    open_events = await event_repo.count_by_status("open")
    critical_events = await event_repo.count_critical_open()
    pending_obs = await outbox_repo.get_pending_count()

    ind_result = await session.execute(select(func.count(Indicator.id)))
    total_indicators = ind_result.scalar_one()

    chat_result = await session.execute(
        select(func.count(Chat.telegram_chat_id)).where(Chat.enabled)
    )
    active_groups = chat_result.scalar_one()

    off_result = await session.execute(select(func.count(Officer.id)).where(Officer.is_active))
    active_officers = off_result.scalar_one()

    return DashboardResponse(
        open_events=open_events,
        critical_events=critical_events,
        pending_observations=pending_obs,
        total_indicators=total_indicators,
        active_groups=active_groups,
        active_officers=active_officers,
    )
