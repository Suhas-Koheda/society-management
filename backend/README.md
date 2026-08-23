# Society Maintenance Tracker — Backend

FastAPI backend for a residential-society maintenance tracker: residents file
complaints (with photos), admins triage them through a strict lifecycle, and
important notices keep everyone informed.

## 1. Project overview

- Residents register, log in, create complaints and view only their own data.
- Admins manage all complaints: filter, paginate, set priority, move status,
  and see full audit history.
- Complaints become **overdue** automatically based on a configurable
  threshold; overdue items surface first in the admin view.
- An admin dashboard aggregates counts by status/category plus overdue count.
- Admins publish notices; important notices are pinned and trigger emails.
- Email notifications fire on complaint status changes and important notices.

## 2. Architecture

```
routers/        thin HTTP layer (validation in, schema out)
services/       business rules, transactions, orchestration
repositories/   SQLAlchemy queries only
models/         SQLAlchemy 2.0 typed models
schemas/        Pydantic request/response models
core/           config, security primitives, auth dependencies, enums
alembic/        migrations (the only way the schema changes)
```

Layering rule of thumb: routers stay thin, services own business logic and
transaction boundaries, repositories never make authorization decisions.

## 3. Tech stack

| Piece      | Choice                                        |
| ---------- | --------------------------------------------- |
| Framework  | FastAPI                                       |
| Language   | Python 3.12+                                  |
| Database   | SQLite (dev), SQLAlchemy 2.0 ORM              |
| Migrations | Alembic                                       |
| Auth       | JWT (PyJWT) + Argon2id password hashing (pwdlib) |
| Settings   | pydantic-settings + `.env`                    |
| Images     | Cloudinary SDK behind a storage abstraction   |
| Email      | Resend HTTP API behind an email abstraction   |
| Tests      | pytest + FastAPI TestClient                   |

## 4. Folder structure

```
backend/
├── alembic/
│   └── versions/
├── app/
│   ├── core/          config.py, security.py, dependencies.py, enums.py
│   ├── db/            database.py (engine, session, Base, utcnow)
│   ├── models/        user, complaint (+history/photos), notice, system_setting
│   ├── schemas/       auth, complaint, admin, notice, dashboard
│   ├── services/      auth, complaint, admin_complaint, photo, storage,
│   │                  notice, settings, overdue, dashboard, email
│   ├── repositories/  complaint_repository, notice_repository
│   └── routers/       auth, complaints, notices, admin
├── tests/
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

## 5. Local setup

### Python version

Python **3.12 or newer**.

### Virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Dependency installation

```bash
pip install -r requirements.txt
```

## 6. Environment variables

Copy the template and fill it in:

```bash
cp .env.example .env
```

Generate a real JWT secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` is git-ignored; never commit real credentials. See `.env.example` for
the full list (`DATABASE_URL`, `JWT_*`, `CLOUDINARY_*`, `EMAIL_*`,
`MAX_UPLOAD_SIZE_MB`).

## 7. SQLite setup

No server needed. The database file is created at `./society.db` on first
migration. Tests use an isolated in-memory SQLite database.

## 8. Alembic migration commands

```bash
alembic upgrade head                              # apply all migrations
alembic revision --autogenerate -m "describe"     # generate from models
alembic check                                     # verify model/db parity
alembic downgrade -1                              # roll back one migration
```

## 9. Running FastAPI

```bash
uvicorn app.main:app --reload
```

## 10. Swagger documentation

With the server running:

- Interactive docs: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Use the **Authorize** button with `Bearer <access_token>` to call protected
endpoints from the UI.

## 11. Running tests

```bash
pytest -q
```

Tests use an in-memory database, fake storage and fake email providers — no
real credentials or network access required.

## 12. Cloudinary setup

1. Create a free account at <https://cloudinary.com>.
2. Copy cloud name / API key / API secret from the dashboard into `.env`.
3. Restart the API. Uploads then store binaries in Cloudinary; without these
   values a console fallback stores nothing externally (useful for local dev).

## 13. Resend/email setup

1. Create a free account at <https://resend.com> and verify a sender domain.
2. Put your API key in `.env`, set `EMAIL_PROVIDER=resend` and `EMAIL_FROM`.
3. With `EMAIL_PROVIDER=console` emails are simply logged instead of sent.
4. Failures are logged and never break committed application state.

## 14. Authentication flow

1. `POST /api/v1/auth/register` → account created with role `resident`
   (email normalized to lowercase; duplicates rejected with 409).
2. `POST /api/v1/auth/login` → returns `{access_token, token_type:"bearer"}`.
3. Send `Authorization: Bearer <token>` on protected calls.
4. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`; invalid/expired tokens
   yield 401.

Passwords are stored as Argon2id hashes and never returned by any endpoint.
Admins cannot self-register — promote roles directly in the database for now.

## 15. Roles

| Role     | Abilities                                                        |
| -------- | ---------------------------------------------------------------- |
| resident | CRUD own complaints, upload/list own complaint photos, read notices |
| admin    | everything residents can do, plus full complaint management, notices CRUD, settings, dashboard |

## 16. Complaint lifecycle

```
OPEN ──▶ IN_PROGRESS ──▶ RESOLVED (terminal, sets resolved_at)
```

- Creation always starts at `OPEN` / priority `LOW`.
- Only those two transitions are allowed; everything else → `409 Conflict`.
- Resolved complaints can never be reopened.
- Every successful transition writes a `ComplaintStatusHistory` row
  (actor = admin, optional note) in the same transaction as the update.
- Priority changes are allowed anytime but are not history events.

## 17. Overdue detection

A non-resolved complaint is **overdue** when:

```
now > created_at + overdue_threshold_days
```

- Threshold lives in the `system_settings` table under
  `overdue_threshold_days` (default **7**, valid range 1–365).
- Nothing is persisted per-complaint — overdue is derived at query time, so
  changing the threshold takes effect immediately everywhere (list filter,
  ordering, dashboard count).

## 18. API endpoint summary

Auth:

| Method | Path                     | Notes                        |
| ------ | ------------------------ | ---------------------------- |
| POST   | `/api/v1/auth/register`  | 201, creates resident        |
| POST   | `/api/v1/auth/login`     | 200, `{access_token, ...}`   |
| GET    | `/api/v1/auth/me`        | current user                 |

Health: `GET /health`.

Resident complaints (all require auth):

| Method | Path                                      | Notes                          |
| ------ | ----------------------------------------- | ------------------------------ |
| POST   | `/api/v1/complaints`                      | 201                            |
| GET    | `/api/v1/complaints`                      | own complaints, newest first   |
| GET    | `/api/v1/complaints/{id}`                 | 404 if not owner               |
| GET    | `/api/v1/complaints/{id}/history`         | oldest → newest                |
| POST   | `/api/v1/complaints/{id}/photos`          | multipart image, ≤5 MB default |
| GET    | `/api/v1/complaints/{id}/photos`          | metadata only                  |

Notices (require auth):

| Method | Path                          | Notes                                    |
| ------ | ----------------------------- | ---------------------------------------- |
| GET    | `/api/v1/notices`             | `?important=&page=&page_size=`           |
| GET    | `/api/v1/notices/{id}`        |                                          |

Admin (require `role=admin`; residents get 403):

| Method | Path                                             | Notes                                  |
| ------ | ------------------------------------------------ | -------------------------------------- |
| GET    | `/api/v1/admin/complaints`                       | filters: status, category, priority, date_from/to, overdue; pagination; overdue-first ordering |
| GET    | `/api/v1/admin/complaints/{id}`                  | includes resident info                 |
| PATCH  | `/api/v1/admin/complaints/{id}/priority`         | LOW/MEDIUM/HIGH                        |
| PATCH  | `/api/v1/admin/complaints/{id}/status`           | strict lifecycle; 409 otherwise        |
| GET    | `/api/v1/admin/complaints/{id}/history`          | includes actor name/email              |
| GET    | `/api/v1/admin/complaints/{id}/photos`           |                                        |
| GET    | `/api/v1/admin/settings/overdue-threshold`       | default 7                              |
| PATCH  | `/api/v1/admin/settings/overdue-threshold`       | 1–365                                  |
| GET    | `/api/v1/admin/dashboard`                        | totals, by_status, by_category, overdue |
| POST   | `/api/v1/admin/notices`                          | 201; important ones email residents    |
| PATCH  | `/api/v1/admin/notices/{id}`                     |                                        |
| DELETE | `/api/v1/admin/notices/{id}`                     | 204                                    |

Status code conventions: 400/422 validation · 401 unauthenticated ·
403 wrong role · 404 missing or not-owned · 409 invalid transition/duplicate
email · 413 oversized upload · 415 unsupported media type · 502 storage outage.

## 19. Database schema

Six application tables plus Alembic's version table. All timestamps are UTC
(naive, produced by a single `utcnow()` helper).

### users
| Column        | Type         | Constraints                        |
| ------------- | ------------ | ---------------------------------- |
| id            | INTEGER      | PK, indexed                        |
| name          | VARCHAR      | unique, indexed                    |
| email         | VARCHAR      | unique, indexed (login identifier) |
| password_hash | VARCHAR      | Argon2id hash, never returned      |
| role          | VARCHAR      | `resident` (default) / `admin`     |
| created_at / updated_at | DATETIME |                          |

### complaints
| Column      | Type    | Notes                                        |
| ----------- | ------- | -------------------------------------------- |
| id          | INTEGER | PK                                           |
| resident_id | INTEGER | FK → users.id, indexed                       |
| category    | VARCHAR | indexed; PLUMBING/ELECTRICAL/CLEANING/SECURITY/MAINTENANCE/OTHER |
| description | TEXT    |                                              |
| status      | VARCHAR | indexed; OPEN → IN_PROGRESS → RESOLVED       |
| priority    | VARCHAR | indexed; LOW/MEDIUM/HIGH                     |
| created_at  | DATETIME | indexed (date filters, ordering)            |
| updated_at  | DATETIME |                                             |
| resolved_at | DATETIME | NULL until resolved                         |

### complaint_status_history
| Column       | Type    | Notes                                    |
| ------------ | ------- | ---------------------------------------- |
| id           | INTEGER | PK                                       |
| complaint_id | INTEGER | FK → complaints.id ON DELETE CASCADE, indexed |
| status       | VARCHAR | the new status                           |
| actor_id     | INTEGER | FK → users.id (who made the change)      |
| note         | TEXT    | optional                                 |
| created_at   | DATETIME | timestamp of the transition             |

### complaint_photos
| Column      | Type     | Notes                                     |
| ----------- | -------- | ----------------------------------------- |
| id          | INTEGER  | PK                                        |
| complaint_id| INTEGER  | FK → complaints.id ON DELETE CASCADE, indexed |
| url         | VARCHAR(500) | public URL from object storage        |
| storage_key | VARCHAR(500) | provider key for cleanup, nullable    |
| created_at  | DATETIME |                                           |

Image binaries live in Cloudinary — SQLite stores metadata only.

### notices
| Column       | Type     | Notes                                   |
| ------------ | -------- | --------------------------------------- |
| id           | INTEGER  | PK                                      |
| title        | VARCHAR(200) |                                     |
| content      | TEXT     |                                         |
| is_important | BOOLEAN  | pinned to top + triggers email          |
| created_by   | INTEGER  | FK → users.id                           |
| created_at / updated_at | DATETIME | composite index (`is_important`, `created_at`) |

### system_settings
key/value store; `overdue_threshold_days` (default 7) drives overdue logic.

Relationships: `User 1—N Complaints / History rows / Notices`;
`Complaint 1—N StatusHistory / Photos`. Deleting a complaint cascades to its
history and photos.

## 20. Deployment (Render example)

A `render.yaml` blueprint is included. Steps:

1. Push this repository to GitHub.
2. In Render: **New → Blueprint**, select the repo.
3. Set `CLOUDINARY_*` and `RESEND_API_KEY`/`EMAIL_PROVIDER` in the Render
   dashboard for real photo/email behavior.
4. Deploy — the start command runs `alembic upgrade head` before serving.

Note: free-tier disks are ephemeral; SQLite resets on redeploy. For a
persistent deployment, attach a disk or switch `DATABASE_URL` to managed
PostgreSQL (the query layer avoids SQLite-specific SQL).
