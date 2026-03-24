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

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Alembic
- **Frontend**: React + TypeScript, Vite
- **Database**: PostgreSQL
- **Cache**: Redis
- **Notifications**: Telegram Bot API
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Package management**: uv (Python), pnpm (JS)

## Branching Strategy

See `docs/process/release-policy.md` for full details.

- `main` — production-ready, protected
- `develop` — integration branch
- `feature/*` — new features
- `bugfix/*` — bug fixes
- `hotfix/*` — production hotfixes
- `docs/*` — documentation changes
- `release/*` — release preparation

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

### User Roles
- **Admin** — full system management
- **Department Head** (Руководитель управления) — sees all departments
- **Team Lead** — manages their specific team within a department
- **HR** — access to reports and analytics
- **Employee** (Сотрудник) — views own profile, self-assessment

### Assessment Process
- 360° assessment: self + peers + team lead + department head
- Frequency: twice per year
- Full history tracking with growth dynamics
- **Default weights**: Head 35%, TL 30%, Self 20%, Peers 15% (configurable per campaign)
- **Aggregation**: `final = head×0.35 + tl×0.30 + self×0.20 + peer_avg×0.15`; missing source weight redistributed proportionally
- **Peer selection**: employee chooses reviewers (min 1), reviewer cannot refuse
- **Deadline extension**: +2 weeks auto-extension for incomplete peer reviews
- **Immutability**: self-assessment locked after submission; manager can return for rework
- **Anonymity**: employee sees aggregated score only; TL sees individual scores within own dept; Head sees all
- **Calibration**: auto-flag when score spread ≥2 levels; calibration phase before finalization
- **Campaign types**: division-wide OR targeted (single department/team)
- **Campaign statuses**: Draft → Active → Collecting → Calibration → Finalized → Archived
- **Mid-campaign joiners**: wait for next cycle
- **Mid-cycle department transfer**: assessed against new department's target profile
- **Staleness**: assessments older than 2 years marked as "stale" in UI

### User Roles (detailed permissions)
- **Admin** — full access: manual scores, delete assessments, configure weights, manage everything
- **Department Head** (Руководитель управления) — sees/assesses all 5 departments, edits target profiles, runs calibration
- **Department Head (отдел)** — sees other departments (read-only), edits own dept target profiles, assesses own dept
- **Team Lead** — assesses own team, sees individual peer scores in own dept, **cannot edit** target profiles but **can propose** changes, can propose competencies
- **HR** — sees all personal data (names, scores) across division, **cannot edit** IDP, can export reports
- **Employee** (Сотрудник) — own data only, aggregated scores only, can propose learning resources

### Competency Catalog Rules
- Common competencies → assessed by ALL departments
- Level descriptions are universal (not department-contextual)
- Deactivated competencies: historical assessments preserved, reactivation by Admin only
- Learning resources: any user can propose → approval by Admin/Head/TL ("second hand" principle)
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
- Unfinished goals **carry over** to next cycle
- Deadlines only for **mandatory competencies**
- Unfulfilled mandatory goal → **trigger flag** (highlighted to TL and Head)
- Goal completion detected **automatically** when assessment score improves in next campaign

### Notifications
- **Dual channel**: Telegram (primary) + email (fallback)
- No Telegram → email only
- User can toggle notification categories: assessment, IDP, career, system

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
- CSV/Excel import for employees and competencies
- Telegram + email notifications (configurable per user)
- Assessment history, growth tracking, staleness marking
- Full search and filtering
- Onboarding wizard for new employees
