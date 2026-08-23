from fastapi import FastAPI

from app.routers import admin, auth, complaints, notices
from app.routers.admin import admin_users_router
from app.db.database import sessionLocal, Base
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select


def seed_admin():
    db = sessionLocal()
    try:
        admin_user = db.scalar(select(User).where(User.email == "admin@society.com"))
        if admin_user is None:
            admin_user = User(
                name="Admin",
                email="admin@society.com",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="Society Maintenance Tracker",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    from app.db.database import engine
    Base.metadata.create_all(bind=engine)
    seed_admin()


app.include_router(auth.router, prefix="/api/v1")
app.include_router(complaints.router, prefix="/api/v1")
app.include_router(notices.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(admin.settings_router, prefix="/api/v1")
app.include_router(admin.dashboard_router, prefix="/api/v1")
app.include_router(admin.admin_notices_router, prefix="/api/v1")
app.include_router(admin_users_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
