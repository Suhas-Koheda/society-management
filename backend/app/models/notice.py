from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean,DateTime,ForeignKey,Index,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.database import Base,utcnow

if TYPE_CHECKING:
    from app.models.user import User

class Notice(Base):
    __tablename__="notices"
    __table_args__=(
        Index("ix_notices_is_important_created_at","is_important","created_at"),
    )

    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    title:Mapped[str]=mapped_column(String(200))
    content:Mapped[str]=mapped_column(Text)
    is_important:Mapped[bool]=mapped_column(Boolean,default=False)
    created_by:Mapped[int]=mapped_column(ForeignKey("users.id"))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)

    author:Mapped["User"]=relationship(back_populates="notices")
