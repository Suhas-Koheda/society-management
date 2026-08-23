from enum import StrEnum


class ComplaintStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class ComplaintPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ComplaintCategory(StrEnum):
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    CLEANING = "CLEANING"
    SECURITY = "SECURITY"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"
