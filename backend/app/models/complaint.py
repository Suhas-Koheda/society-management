from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime,ForeignKey,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.database import Base,utcnow

if TYPE_CHECKING:
    from app.models.user import User

class Complaint(Base):
    __tablename__="complaints"

    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    resident_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    category:Mapped[str]=mapped_column(String(100),index=True)
    description:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(50),default="open",index=True)
    priority:Mapped[str]=mapped_column(String(20),default="medium",index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow,index=True)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)
    resolved_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)

    resident:Mapped["User"]=relationship(back_populates="complaints")
    status_history:Mapped[list["ComplaintStatusHistory"]]=relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
    )
    photos:Mapped[list["ComplaintPhoto"]]=relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
    )

class ComplaintStatusHistory(Base):
    __tablename__="complaint_status_history"

    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    complaint_id:Mapped[int]=mapped_column(ForeignKey("complaints.id",ondelete="CASCADE"),index=True)
    status:Mapped[str]=mapped_column(String(50))
    actor_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    note:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)

    complaint:Mapped["Complaint"]=relationship(back_populates="status_history")
    actor:Mapped["User"]=relationship(back_populates="status_history")

class ComplaintPhoto(Base):
    __tablename__="complaint_photos"

    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    complaint_id:Mapped[int]=mapped_column(ForeignKey("complaints.id",ondelete="CASCADE"),index=True)
    url:Mapped[str]=mapped_column(String(500))
    storage_key:Mapped[str|None]=mapped_column(String(500),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)

    complaint:Mapped["Complaint"]=relationship(back_populates="photos")
