# Changelog

All notable changes to Matrix are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.4.0] — 2026-03-25 — Phase 2 Complete: Assessment MVP

### Added

**Week 9 — Campaign lifecycle**
- `POST /api/v1/assessments/campaigns/{id}/activate|close|finalize|archive` — status machine transitions (Draft→Active→Calibration→Finalized→Archived)
- Weighted aggregation engine: computes `AggregatedScore` with proportional weight redistribution when assessor types are missing
- `GET /api/v1/assessments/campaigns/{id}/progress` — returns total/completed/pending counts and completion percentage
- `GET /api/v1/assessments/campaigns/{id}/scores` — aggregated scores per user×competency after finalization
- `PUT /api/v1/assessments/campaigns/{id}/weights` — configure assessor weights per campaign (default: DH 35%, TL 30%, self 20%, peer 15%)
- `CampaignsPage` — list campaigns with status filter + create modal
- `CampaignDetailPage` — progress bar, lifecycle action buttons, assessments table

**Week 10 — 360° peer selection and task tracking**
- `POST /api/v1/assessments/campaigns/{id}/peers` — employee sets peer reviewers (PeerSelection model)
- `GET /api/v1/assessments/campaigns/{id}/peers` — get own peer list for campaign
- `GET /api/v1/assessments/my-tasks` — pending assessments where current user is assessor
- `MyTasksPage` — list of pending assessment tasks, click to open form

**Week 11 — Assessment history**
- `GET /api/v1/users/{id}/assessment-history` — all AggregatedScores across campaigns with self/tl/dh/peer component breakdown

**Week 12 — Visualizations**
- `RadarChart` component (Recharts) with current + target level overlay
- `GapAnalysisPage` — target profile selector, current vs required levels, color-coded gap badges, completion progress bar
- `UserProfilePage` — embedded radar chart of competency scores + Gap-анализ navigation button

### Tests
- 8 new tests: `test_campaign_lifecycle.py` (full lifecycle, invalid transitions, progress, aggregation, weights, RBAC)
- **Total: 141 tests, coverage 90%**

### PRs
- [#13](https://github.com/666bes666/matrix/pull/13) — Phase 2 complete

---

## [0.3.0] — 2026-03-25 — Phase 1 Complete: Weeks 4–8

### Added

**Week 4 — Employee Profiles**
- `GET /api/v1/users` — list users with search, department, team, role, is_active filters
- `POST /api/v1/users` — create user (admin, head only)
- `GET /api/v1/users/me` — current user profile
- `GET /api/v1/users/{id}` — user detail (scope-filtered)
- `PATCH /api/v1/users/{id}` — update user (scope-filtered by role)
- `POST /api/v1/users/{id}/activate` / `deactivate` — toggle active state (admin/head)
- Frontend: `UsersPage` with DataTable, search and filters; `UserProfilePage` detail view; `RoleBadge` component

**Week 5 — Competency Catalog**
- `GET /api/v1/competencies/categories` — list categories
- `GET /api/v1/competencies` — list with filters (category, department, is_common, is_archived, search)
- `POST /api/v1/competencies` — create (admin, head, department_head)
- `GET/PATCH /api/v1/competencies/{id}` — read/update
- `POST /api/v1/competencies/{id}/archive` / `unarchive` — soft archive (admin, head)
- `PUT /api/v1/competencies/{id}/criteria` — upsert level descriptions (0-4)
- Frontend: `CompetenciesPage` grouped by category; inline create/edit with criteria editor

**Week 6 — Assessment Foundation**
- `POST /api/v1/assessments/campaigns` — create campaign (admin, head, dept_head)
- `GET /api/v1/assessments/campaigns` — list campaigns with status filter
- `GET /api/v1/assessments/campaigns/{id}` — campaign detail
- `POST /api/v1/assessments` — create assessment (admin, dept_head, team_lead)
- `GET /api/v1/assessments` — list with campaign_id / assessee_id filters
- `GET /api/v1/assessments/{id}` — assessment detail with scores
- `POST /api/v1/assessments/{id}/scores` — submit scores (upsert, draft support)
- `GET /api/v1/target-profiles` — list target profiles with department filter
- `POST /api/v1/target-profiles` — create (admin, head, dept_head)
- `GET/PATCH /api/v1/target-profiles/{id}` — read/update
- `DELETE /api/v1/target-profiles/{id}` — delete (admin, head)
- `PUT /api/v1/target-profiles/{id}/competencies` — set required competencies with levels
- `GET /api/v1/target-profiles/{id}/gap/{user_id}` — gap analysis vs AggregatedScore
- Frontend: `TargetProfilesPage`, `AssessmentFormPage` with radio 0–4, draft/submit

**Week 7 — Competency Matrix UI**
- `GET /api/v1/analytics/matrix` — returns scope-filtered `{users, competencies, scores}` dict
- Frontend: `MatrixPage` with department/category filter selects
- `MatrixGrid` component: sticky row/column headers, color-coded cells (0=red → 4=blue), tooltips
- Navigation sidebar wired with all Phase 1 pages; `App.tsx` routes registered

**Week 8 — RBAC Enforcement**
- `check_department_access(user, dept_id)` — dept_head restricted to own department
- `check_team_access(user, team_dept_id)` — team_lead restricted to own department
- `departments.py`: dept_head can only create/update teams within own department
- `target_profiles.py`: dept_head can only create/update profiles within own department
- `usePermissions.ts` frontend hook: `canCreateUser`, `canEditCompetency`, `canCreateCampaign`, etc.

### Tests
- Week 4: 23 tests (`test_users.py`)
- Week 5: 19 tests (`test_competencies.py`)
- Week 6: 12 + 12 tests (`test_target_profiles.py`, `test_assessments.py`)
- Week 7: 9 tests (`test_analytics.py`)
- Week 8: 26 tests (`test_rbac.py`)
- **Total: 133 tests, coverage 92%**

### PRs
- [#8](https://github.com/666bes666/matrix/pull/8) — Week 4: User profiles
- [#9](https://github.com/666bes666/matrix/pull/9) — Week 5: Competency catalog
- [#10](https://github.com/666bes666/matrix/pull/10) — Week 6: Target profiles + assessments
- [#11](https://github.com/666bes666/matrix/pull/11) — Week 7: Matrix UI
- [#12](https://github.com/666bes666/matrix/pull/12) — Week 8: RBAC enforcement

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

[Unreleased]: https://github.com/666bes666/matrix/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/666bes666/matrix/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/666bes666/matrix/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/666bes666/matrix/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/666bes666/matrix/releases/tag/v0.1.0
