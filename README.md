# Society Maintenance Tracker

Full-stack society complaint management system with admin dashboard.

**Live**: https://society-management-production-e949.up.railway.app

## Stack
- **Backend**: Python / FastAPI / SQLAlchemy / SQLite
- **Frontend**: React 19 / Vite / TypeScript / TanStack Query
- **Deploy**: Railway (single Dockerfile)

## Quick Start

### Docker (local)
```bash
docker compose up -d
```
Open **http://localhost**

### Manual
```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
pnpm run dev
```

## Default Admin

- **Email**: `admin@society.com`
- **Password**: `admin123`

## Features

- Landing page with role overview
- Resident registration and login
- Complaint creation with category, description, and photo upload
- Full status history tracking (OPEN -> IN_PROGRESS -> RESOLVED)
- Admin dashboard with stats (by status, category, overdue count)
- Admin complaint management (status updates, priority assignment)
- Admin notice board with important notice email notifications
- Configurable overdue threshold
- User management (promote/demote admins)
