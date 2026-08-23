# Society Maintenance Tracker

Full-stack society complaint management system with admin dashboard.

## Stack
- **Backend**: Python / FastAPI / SQLAlchemy / SQLite
- **Frontend**: React 19 / Vite / TypeScript / TanStack Query
- **Infra**: Docker Compose (nginx reverse proxy)

## Quick Start

```bash
docker compose up -d
```

Open **http://localhost**

## Default Admin

- **Email**: `admin@society.com`
- **Password**: `admin123`

## Features

- Resident registration and login
- Complaint creation with category, description, and photo upload
- Full status history tracking (OPEN -> IN_PROGRESS -> RESOLVED)
- Admin dashboard with stats (by status, category, overdue count)
- Admin complaint management (status updates, priority assignment)
- Admin notice board with important notice email notifications
- Configurable overdue threshold
- User management (promote/demote admins)
