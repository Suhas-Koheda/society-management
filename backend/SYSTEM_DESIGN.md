# System Design — Society Maintenance Tracker

This write-up covers the four areas the project brief calls out: the
complaint history model, overdue detection, photo handling, and the
notification flow. The backend is FastAPI + SQLAlchemy 2.0 + SQLite, layered
as routers → services → repositories, with Pydantic schemas at the boundary
and Alembic owning the schema.

## Complaint history model

A complaint is a row in `complaints` whose `status` moves through a strict
lifecycle: `OPEN → IN_PROGRESS → RESOLVED`. Transitions are encoded in one
place — `ALLOWED_STATUS_TRANSITIONS` in the admin service — as a dict of
allowed successors (`RESOLVED` maps to an empty set, making it terminal).
Anything else is rejected with `409 Conflict`, so a resolved complaint can
never be reopened.

Every successful transition writes a `complaint_status_history` row inside
the *same database transaction* as the status update: service calls flush
both inserts, then commits once. If history insertion fails, neither change
survives — verified by a regression test that injects a repository failure.
Each history row records `status` (new value), `actor_id` (the admin from
the JWT), an optional `note`, and `created_at`. The complaint's own
`updated_at` is maintained by an `onupdate` hook, while `created_at` is set
once at creation; both come from a single shared UTC helper so the whole app
uses one time convention.

History is append-only: there is no update path for it anywhere. Residents
read it oldest-first for their own complaints (404-masked if not theirs);
admins read the full timeline joined to users to show actor name/email.
Priority changes deliberately do **not** create history rows — that table
represents the status lifecycle only.

## Overdue detection

Overdue is never stored. Storing an `is_overdue` boolean would go stale the
moment time passes or the policy changes. Instead it is derived:

```
overdue ⇔ status ≠ RESOLVED AND now > created_at + threshold_days
```

The threshold lives in `system_settings` under `overdue_threshold_days`
(default 7, valid 1–365) with one accessor that safely parses, validates,
and falls back to defaults — no scattered `int()` conversions.

Because the threshold is known at query time, the comparison is rewritten
into a portable predicate against a precomputed cutoff:
`status != 'RESOLVED' AND created_at < now − threshold`. This is plain
SQLAlchemy column math — no vendor functions — so it runs identically on
SQLite today and PostgreSQL tomorrow. The same predicate powers four things
from one definition in `overdue_service.py`: the pure `is_overdue()`
function (unit-testable with injected clocks), the `?overdue=` list filter,
the "overdue first" ordering expression, and the dashboard's
`overdue_count` aggregate. Changing the threshold takes effect immediately
everywhere. Admin listing orders by overdue-first, then HIGH > MEDIUM > LOW
priority (a CASE ranking), then newest — deterministic via id tiebreaks —
with offset/limit pagination capped at 100 per page.

## Photo handling

Binaries never touch the relational store. `complaint_photos` holds only
metadata: `complaint_id` (FK, indexed, cascade), `url`,
`storage_key` (provider's key, used for cleanup), `created_at`.

Uploads flow through a storage abstraction (`StorageBackend`) with two
implementations: Cloudinary for production and a console fallback for local
development; tests inject a fake via FastAPI dependency override. Routers
never import Cloudinary. Validation is server-side and paranoid: size cap
(configurable, default 5 MB → 413), magic-byte sniffing of JPEG/PNG/WebP
signatures cross-checked against the declared content type (→ 415). Client
filenames are ignored entirely, which removes path-traversal concerns.

The upload sequence is: authenticate → verify ownership (404-masked) →
validate bytes → upload → insert metadata → commit. If the DB insert fails
after a successful upload, the service rolls back and best-effort deletes
the remote object, minimizing orphans; if the provider fails, no record is
created (502 to the client).

## Notification flow

Emails use the same abstraction pattern. `email_service.py` defines an
`EmailProvider` interface with a Resend implementation (plain HTTPS API —
no SDK lock-in) and a console logger default; configuration comes entirely
from environment variables.

The critical rule is ordering: notifications fire strictly **after** the
database transaction commits, never before, and every send is wrapped so
failures are logged but never rolled back into application state or leaked
to API clients. Two events trigger mail: an admin moving a resident's
complaint status (recipient gets name, complaint ID, category, new status,
admin note, timestamp), and creation — or promotion — of an important
notice (fanned out to all users). Normal notices stay silent. Tests replace
the provider with a recording fake through dependency injection, asserting
that correct transitions send exactly one well-formed message, invalid
transitions send nothing, and a crashing provider leaves committed state
intact.
