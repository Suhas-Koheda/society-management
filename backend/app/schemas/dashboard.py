from pydantic import BaseModel

from app.core.enums import ComplaintCategory, ComplaintStatus


class DashboardResponse(BaseModel):
    total_complaints: int
    by_status: dict[ComplaintStatus, int]
    by_category: dict[ComplaintCategory, int]
    overdue_count: int
