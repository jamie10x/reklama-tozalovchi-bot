from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_officer, get_db
from app.database.repositories.events import SecurityEventRepository
from app.database.secadmin_models import Officer

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/events")
async def export_events(
    session: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    repo = SecurityEventRepository(session)
    events = await repo.list(limit=200)
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    header = [
        "id",
        "event_number",
        "chat_id",
        "event_type",
        "severity",
        "score",
        "status",
        "created_at",
    ]
    writer.writerow(header)
    for e in events:
        writer.writerow(
            [
                str(e.id),
                e.event_number,
                e.chat_id,
                e.event_type,
                e.severity,
                e.score,
                e.status,
                e.created_at,
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=security_events.csv"},
    )
