from pydantic import BaseModel


class DashboardResponse(BaseModel):
    open_events: int
    critical_events: int
    pending_observations: int
    total_indicators: int
    active_groups: int
    active_officers: int
