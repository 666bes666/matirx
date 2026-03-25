# Matrix — Competency Matrix Platform

## Project Overview

Matrix is an internal web application for managing employee competency matrices.
It is built for the Dynamic Infrastructure Portal support division at Sber (private cloud for internal Sber users).

The division has 5 departments with ~10-50 employees total. The product tracks competencies,
enables 360° assessments, visualizes skill gaps, and supports career path planning across departments.

## Repository Structure

```
docs/
  business/           # Business documents (RU)
    product-vision.md
    market-requirements.md
    business-requirements.md
    business-plan.md
  product/            # Product documents (RU)
    roadmap.md
    product-requirements.md
    product-backlog.md
  technical/          # Technical documents (EN)
    technical-specification.md
    risk-register.md
  process/            # Process documents (EN)
    release-policy.md
src/                  # Application source code (when development begins)
tests/                # Test suite
```

## Tech Stack (planned)

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **Frontend**: React 18+, TypeScript, Vite, TanStack Query + Zustand, Mantine UI, Recharts
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Task Queue**: Celery + Redis (campaign deadlines, notifications, IDP checks)
- **Notifications**: Telegram Bot API + in-app (polling). No email in MVP
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Package management**: uv (Python), pnpm (JS)
- **Linting**: ruff (Python), ESLint + Prettier (JS)

## Branching Strategy

See `docs/process/release-policy.md` for full details.

**GitHub Flow:**
- `main` — production-ready, protected
- `feature/*` — new features
- `fix/*` — bug fixes
- `docs/*` — documentation changes

## Development Commands

```bash
# Backend
cd src/backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend
cd src/frontend
pnpm install
pnpm dev

# Tests
uv run pytest tests/ -q

# Docker
docker compose up -d
```

## Code Conventions

- Python: no comments in source files, no docstrings required
- Follow PEP 8, use ruff for linting
- TypeScript: strict mode, ESLint + Prettier
- All PRs require at least one review
- Commits follow Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## Key Domain Concepts

### Departments (5)
1. **First Line Support** (Первая линия) — basic portal support, quotas, known bugs
2. **Duty Shift** (Дежурная смена) — deeper troubleshooting, Ansible, vCloud Director, networking, incidents
3. **Business Logic** (Бизнес-логика) — portal business logic verification, resource provisioning
4. **Second Line Support** (Вторая линия) — SRE/DevOps, logs, metrics, code changes, DB operations
5. **Jenkins CDP Support** (Сопровождение Jenkins CDP) — Jenkins automation

### Competency Categories
- **Hard Skills** — technical skills (Linux, networking, K8s, cloud, scripting, etc.)
- **Soft Skills** — communication, teamwork, leadership
- **Processes** — ITIL, incident management, change management
- **Domain Knowledge** — portal product knowledge, internal systems, business processes

### Proficiency Levels (5)
0. None (Нет знаний)
1. Novice (Новичок)
2. Basic (Базовый)
3. Advanced (Продвинутый)
4. Expert (Эксперт)

### User Roles (6 roles)
- **Admin** — full system management, audit log, user CRUD, system configuration
- **Head** (Руководитель управления) — **informational role**: sees all 5 departments (read-only for assessments/calibration), creates campaigns, manages competency catalog. Does NOT assess employees, does NOT calibrate
- **Department Head** (Руководитель отдела) — sees own department + read-only on others, edits own target profiles, manages competencies for own department
- **Team Lead** — assesses own team, sees individual peer scores in own dept, proposes competencies/changes
- **HR** — sees all personal data (names, scores) across division, exports reports, CSV import, cannot edit IDP
- **Employee** (Сотрудник) — views own profile, self-assessment, aggregated scores only

### Assessment Process
- 360° assessment: self + peers + team lead + department head
- Frequency: twice per year
- Full history tracking with growth dynamics
- **Default weights**: Department Head 35%, TL 30%, Self 20%, Peers 15%. Head does NOT assess. (configurable per campaign)
- **Aggregation**: `final = dept_head×0.35 + tl×0.30 + self×0.20 + peer_avg×0.15`; missing source weight redistributed proportionally among remaining
- **Peer selection**: employee chooses reviewers (min 1), reviewer cannot refuse
- **Deadline extension**: +2 weeks auto-extension for incomplete peer reviews
- **Immutability**: self-assessment locked after submission; manager can return for rework
- **Anonymity**: employee sees aggregated score only; TL sees individual scores within own dept; Department Head sees all within own dept; Head sees aggregated scores across all depts (read-only)
- **Calibration**: auto-flag when score spread ≥2 levels; Department Head calibrates (Head has read-only view of flags)
- **Campaign types**: division-wide OR targeted (single department/team)
- **Campaign statuses**: Draft → Active → Collecting → Calibration → Finalized → Archived
- **Mid-campaign joiners**: wait for next cycle
- **Mid-cycle department transfer**: assessed against new department's target profile
- **Staleness**: assessments older than 2 years marked as "stale" in UI

### User Roles (detailed permissions)
- **Admin** — full access: manual scores, delete assessments, configure weights, manage everything, audit log
- **Head** (Руководитель управления) — **informational**: sees all 5 departments (read-only for assessments), edits target profiles, manages competency catalog, creates campaigns. Does NOT assess, does NOT calibrate
- **Department Head** (Руководитель отдела) — sees other departments (read-only), edits own dept target profiles, **assesses own dept (weight 0.35)**, manages competencies for own dept, creates campaigns for own dept, **runs calibration for own dept**
- **Team Lead** — assesses own team, sees individual peer scores in own dept, **cannot edit** target profiles but **can propose** changes, can propose competencies, creates IDP
- **HR** — sees all personal data (names, scores) across division, **cannot edit** IDP, can export reports, CSV import
- **Employee** (Сотрудник) — own data only, aggregated scores only, can propose learning resources

### Competency Catalog Rules
- Common competencies (`is_common=true`) → mandatory for ALL employees (soft skills, ITIL)
- Level names are universal: None/Novice/Basic/Advanced/Expert. Level **criteria descriptions are per-competency** (table `competency_level_criteria`)
- 5 levels (0-4), strict, same for all competencies
- Catalog management: Admin + Head + Department Heads (own department)
- Deactivated competencies: Admin chooses — archive (`is_archived=true`, visible in history) or migrate scores to another competency
- Versioning: audit_log tracks description changes, scores are NOT versioned
- Recommended 15-20 competencies per target profile (no hard limit); radar chart groups by category
- Learning resources: TL and above add freely; employees propose via resource_proposals with moderation
- Resources linked to competency + target_level (e.g., "Kubernetes Level 2→3")
- Resource deletion: any user can request → confirmation by Admin/Head/TL

### Career Paths Rules
- Employees **can skip** departments (e.g., First Line → SRE directly)
- Readiness threshold: **90%** of target profile (mandatory competencies must be 100%)
- Competencies split into **mandatory** (must be 100%) and **desirable** (count toward 90%)
- Transition requires: competency threshold + manager approval + HR approval + vacancy + min tenure
- Paths are **bidirectional** (can move back)
- Jenkins CDP is a **side branch**: any dept → Jenkins CDP; Jenkins CDP → Second Line (SRE) only

### IDP Rules
- **Bidirectional initiation**: employee proposes → TL approves, OR TL creates → employee approves
- Disagreements → escalation to Department Head
- Unfinished goals **carry over** semi-automatically: system proposes transfer, TL confirms each goal
- Deadlines only for **mandatory competencies**
- Unfulfilled mandatory goal → **trigger flag** (highlighted to TL and Head)
- Goal completion: auto-detected when assessment score >= target_level → status `pending_completion` + TL notification for manual confirmation

### Notifications
- **MVP**: Telegram (primary) + in-app (table `notifications`, polling 30s, badge on icon)
- **No email in MVP** — email fallback planned for future versions
- Telegram Bot: long polling (dev), webhook (prod)
- Telegram linking: user sends `/start <code>` to bot (code from profile), bot saves `chat_id`
- User can toggle notification categories: assessment, IDP, career, system (all toggleable, except critical from Admin)

### Onboarding (new employee)
Wizard on first login: fill profile → view target profile → initial self-assessment → see gap analysis → recommended resources

### Search & Filtering
Full filtering system:
- By employees: department, team, role, competency level, gap presence
- By competencies: category, level, staleness
- By campaigns: status, period, department
- Example queries: "all employees with gap in Kubernetes", "unassessed in current cycle", "ready for SRE transition"

### Key Features (MVP)
- Competency catalog with learning resources + proposal/moderation workflow
- Employee profiles with department/role assignment
- Target competency profiles for roles (gap analysis)
- Individual development plans (IDP) with trigger flags
- 360° assessment workflow with calibration phase
- Radar charts + heatmaps + Excel/PDF export
- Career path visualization (cross-department transitions)
- CSV/Excel import (template download + upload) for employees and competencies
- Telegram + in-app notifications (configurable per user)
- Assessment history, growth tracking, staleness marking
- Full search and filtering
- Onboarding wizard for new employees

### Authentication & Bootstrap
- **Bootstrap**: CLI command `create-superuser` (first deploy)
- **Registration**: free self-registration, account inactive until Admin/HR confirms
- **Access token**: 30 minutes, stored in memory (JS variable)
- **Refresh token**: 7 days, httpOnly cookie, silent refresh on page reload
- **Password reset**: via Telegram bot (no SMTP in MVP)
- **Account lockout**: Redis counter, 5 attempts → 15 min block (429), auto-unlock by TTL

### Assessment UX
- **Peer selection**: 3-day window after campaign activation, min 1, max 5 peers
- **Cross-department peers**: allowed
- **Draft saving**: server-side auto-save every 30s
- **Mass assessment UX**: TL chooses from 3 modes — (A) per employee, (B) matrix grid, (C) per competency
- **Aggregation**: weighted average only (no arithmetic mean or median)

### Soft Delete Strategy
- **Soft delete**: users (`is_active`), competencies (`is_archived`), campaigns (status `archived`), development_plans (`is_archived`)
- **No delete**: departments (5 preset, cannot be deleted)
- **Hard delete + checks**: teams (must be empty), learning_resources (cascade), career_paths, career_path_requirements

### Seed Data Strategy
- **Production**: 5 departments + competency catalog + target profiles + proficiency levels 0-4
- **Dev/Staging**: + test users + demo campaign with scores
- Implementation: `seed.py` script with `--demo` flag

### Frontend Architecture
- **State**: TanStack Query (server) + Zustand (client)
- **UI Library**: Mantine
- **Charts**: Recharts
- **Language**: Russian only (no i18n)
- **Mobile**: Mobile-first design
- **Testing**: Vitest (unit for calculations) + React Testing Library (critical components: forms, auth)

### Branching Model
- **GitHub Flow** (NOT Git Flow)
- `main` — production-ready, protected
- `feature/*`, `fix/*`, `docs/*` — branch from main, PR to main
- No `develop`, `release/*`, `hotfix/*` branches
- Staging deploys from main after merge
- Production deploys on git tag

### Infrastructure
- **Docker Compose (dev)**: 7 services — postgres, redis, backend, frontend, celery-worker, celery-beat, telegram-bot. In dev: telegram-bot uses long polling (separate service). In prod: webhook mode (part of FastAPI)
- **Task scheduler**: Celery + Redis (campaign deadlines, auto-extend, reminders, IDP checks)
- **Phase 0 order**: Infrastructure-first — Docker + CI/CD + DB + staging + backups → backend + frontend parallel → auth + seed

### Hosting
- **Yandex Cloud**: Compute Instance (VM) + Managed PostgreSQL + Container Registry + Object Storage (backups) + Lockbox (secrets)

### Architecture Decision Records
See `docs/technical/adr-001-implementation-decisions.md` for all 50 implementation decisions with rationale.
