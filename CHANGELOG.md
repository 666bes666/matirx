# Changelog

All notable changes to Matrix are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Phase 1 Week 4 — User profiles CRUD (planned)

---

## [0.2.0] — 2026-03-25 — Phase 1 Week 3: Organizational Structure

### Added

**Backend — Department API**
- `GET /api/v1/departments` — list all departments with nested teams
- `POST /api/v1/departments` — create department (admin, head)
- `GET /api/v1/departments/{id}` — get department with teams
- `PATCH /api/v1/departments/{id}` — update department (admin, head)
- `DELETE /api/v1/departments/{id}` — delete department (admin only)

**Backend — Team API**
- `GET /api/v1/departments/{id}/teams` — list teams in department
- `POST /api/v1/departments/{id}/teams` — create team (admin, head)
- `GET /api/v1/departments/{dept_id}/teams/{team_id}` — get team
- `PATCH /api/v1/departments/{dept_id}/teams/{team_id}` — update (admin, head)
- `DELETE /api/v1/departments/{dept_id}/teams/{team_id}` — delete (admin)

**Business rules enforced**
- 5 preset departments (First Line, Duty Shift, Business Logic, Second Line, Jenkins CDP)
  cannot be deleted — returns 403
- Teams cannot be deleted if they have active users — returns 409
- Department names and team names within a department must be unique — returns 409

**Tests**
- 18 new tests in `tests/backend/test_departments.py`
- Total backend tests: 32, coverage: 87.79%

### Changed
- `app/api/router.py` — registered departments router under `/api/v1`

---

## [0.1.0] — 2026-03-25 — Phase 0: Foundation

### Added

**Infrastructure**
- Docker Compose for local development (7 services: postgres, redis, backend,
  frontend, celery-worker, celery-beat, telegram-bot)
- Production docker-compose with `restart: always` and named image tags
- Backend Dockerfile: `python:3.12-slim` + `uv`
- Frontend Dockerfile: multi-stage (`node:20-alpine` build + `nginx:alpine` serve)
- Nginx reverse proxy: `/api/*` → backend:8000, `/*` → frontend static

**CI/CD (GitHub Actions)**
- `ci.yml`: lint (ruff + ESLint) → typecheck (mypy + tsc) → test (pytest ≥80% + vitest) → build Docker images
- `deploy.yml`: staging deploy on push to main, production on git tag `v*`
- PR template with self-review checklist

**Backend**
- FastAPI application with CORS middleware, lifespan, structured error handlers
- Pydantic Settings for environment variable management
- Async SQLAlchemy engine (pool_size=10, max_overflow=20) + session dependency
- Redis async pool + dependency
- JWT auth: HS256 access tokens (30 min) + refresh tokens (7 days, httpOnly cookie)
- bcrypt password hashing (rounds=12) with strength validation
- Auth dependencies: `get_current_user`, `require_roles`, `require_active_user`
- Pagination: `PaginationParams` + `paginate()` helper
- 25+ SQLAlchemy models: User, Department, Team, Competency, CompetencyCategory,
  TargetProfile, AssessmentCampaign, Assessment, AssessmentScore, AggregatedScore,
  AssessmentWeight, CalibrationFlag, CalibrationAdjustment, PeerSelection,
  DevelopmentPlan, DevelopmentGoal, LearningResource, GoalResource,
  CareerPath, CareerPathRequirement, CompetencyProposal, ResourceProposal,
  Notification, AuditLog
- `pg_enum()` helper for correct PostgreSQL enum value mapping
- Alembic initial migration with all tables, enum types, indexes, constraints
- Auth API: `POST /auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`, `GET /auth/me`
- System API: `GET /system/health` (checks DB + Redis connectivity)
- Celery with Redis broker + beat schedule (daily pg_backup at 03:00)
- Backup task with 3 retries and exponential backoff
- Telegram bot skeleton with long polling and `/start <code>` handler
- CLI: `create-superuser` command
- Seed script: 5 departments, competency catalog; `--demo` flag adds test users and demo campaign

**Frontend**
- React 18 + TypeScript + Vite
- Mantine UI + TanStack Query + Zustand + Axios
- Axios client: request interceptor (attach JWT), response interceptor (silent refresh on 401)
- Auth store (Zustand): `user`, `accessToken`, `isAuthenticated`, `setAuth`, `clearAuth`
- Protected route with silent refresh on mount
- Pages: Login, Register, Dashboard
- AppLayout: sidebar with role-based navigation + header with user menu

**Tests**
- `conftest.py`: `NullPool` async engine, per-test Redis client, factory fixtures
- `test_health.py`: health check endpoint
- `test_auth.py`: login success, wrong password (401), inactive account (403),
  lockout after 5 attempts (429), register, token refresh, logout with jti blacklist,
  expired token (401), password strength validation
- 14 tests passing, backend coverage: 81.65%

### Technical decisions
- `bcrypt` library used directly instead of `passlib` (passlib 1.7.4 incompatible with bcrypt 5.x)
- `NullPool` in test engine to avoid asyncpg event-loop binding issues
- Per-test `aioredis.from_url()` fixture to avoid module-level Redis singleton conflicts
- Test emails use `@example.com` (email-validator rejects `.local` TLD since v2.0)

---

[Unreleased]: https://github.com/666bes666/matrix/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/666bes666/matrix/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/666bes666/matrix/releases/tag/v0.1.0
