from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime,String
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.database import Base,utcnow

if TYPE_CHECKING:
    from app.models.complaint import Complaint, ComplaintStatusHistory
    from app.models.notice import Notice

class User(Base):
    __tablename__="users"

    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    name:Mapped[str]=mapped_column(String,unique=True,index=True)
    email:Mapped[str]=mapped_column(String,unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String)
    role:Mapped[str]=mapped_column(String,default="user")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)

    complaints:Mapped[list["Complaint"]]=relationship(back_populates="resident")
    status_history:Mapped[list["ComplaintStatusHistory"]]=relationship(back_populates="actor")
    notices:Mapped[list["Notice"]]=relationship(back_populates="author")
