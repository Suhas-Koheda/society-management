from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker

from app.core.config import get_settings

DATABASE_URL=get_settings().DATABASE_URL

_connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {}

engine=create_engine(DATABASE_URL,connect_args=_connect_args)

sessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

class Base(DeclarativeBase):
    pass

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def get_db():
    db=sessionLocal()
    try:
        yield db
    finally:
        db.close()
