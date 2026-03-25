# Release Policy and Pipeline

**Project:** Matrix -- Competency Matrix Web Application
**Developer:** Solo developer with AI assistance
**Hosting:** Yandex Cloud
**Last updated:** 2026-03-24

---

## Table of Contents

1. [Branching Strategy](#1-branching-strategy)
2. [Versioning](#2-versioning)
3. [Commit Convention](#3-commit-convention)
4. [Pull Request Process](#4-pull-request-process)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Environments](#6-environments)
7. [Release Process](#7-release-process)
8. [Hotfix Process](#8-hotfix-process)
9. [Database Migrations](#9-database-migrations)
10. [Rollback Strategy](#10-rollback-strategy)

---

## 1. Branching Strategy

The project follows **GitHub Flow** -- a simplified branching model with a single long-lived branch and short-lived feature branches.

### Branch Types

| Branch | Purpose | Branches from | Merges into | Deploys to |
|---|---|---|---|---|
| `main` | Production-ready code | -- | -- | Staging (on merge), Production (on tag) |
| `feature/*` | New features | `main` | `main` | -- |
| `fix/*` | Bug fixes | `main` | `main` | -- |
| `docs/*` | Documentation-only changes | `main` | `main` | -- |

### Branch Naming Convention

- `feature/US-XXX-short-desc` -- new feature tied to a user story
- `fix/US-XXX-short-desc` -- bug fix tied to an issue
- `docs/topic` -- documentation changes

### Branch Protection Rules

- **`main`** -- protected. Direct pushes are forbidden. Changes only via PRs. Requires passing CI checks.

### Branching Flow Diagram

```
main        ──●──────●──────●──────●──────●──tag v1.0──●──────●──tag v1.1──→
              │      ↑      │      ↑      ↑                   ↑
              │      │      │      │      │                   │
feature/*     ●──●───┘      │      │      │                   │
                            │      │      │                   │
fix/*                       ●──●───┘      │                   │
                                          │                   │
docs/*                                    ●───────────────────┘
```

**Reading the diagram:**

- Arrows (`→`) indicate the direction of time.
- `●` marks a commit or branch point.
- `↑` indicates a squash merge back into `main` via PR.
- All branches are short-lived and branch from `main`, merge back into `main`.
- Production deploys happen only when a version tag (`v*`) is pushed on `main`.
- Staging deploys happen automatically on every merge to `main`.

---

## 2. Versioning

The project uses **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`).

| Component | When to increment | Example |
|---|---|---|
| **MAJOR** | Breaking changes to the API, data model, or user-facing contracts | `1.0.0` → `2.0.0` |
| **MINOR** | New features that are backwards compatible | `1.0.0` → `1.1.0` |
| **PATCH** | Bug fixes, minor corrections, no feature changes | `1.1.0` → `1.1.1` |

### Pre-release Versions

During release preparation, pre-release tags may be used:

- `1.2.0-rc.1` -- release candidate 1
- `1.2.0-rc.2` -- release candidate 2

### Version Sources

- Git tags are the single source of truth for versioning.
- Tags follow the format: `v{MAJOR}.{MINOR}.{PATCH}` (e.g., `v1.3.0`).

---

## 3. Commit Convention

All commits must follow the **Conventional Commits** specification (v1.0.0).

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation-only changes |
| `refactor` | Code refactoring (no feature or fix) |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks (dependencies, configs) |
| `ci` | CI/CD pipeline changes |
| `perf` | Performance improvements |

### Scopes

Use scopes to indicate the affected area of the codebase:

- `feat(api):` -- backend API changes
- `fix(ui):` -- frontend/UI bug fix
- `refactor(models):` -- data model refactoring
- `ci(docker):` -- Docker-related CI changes
- `docs(process):` -- process documentation updates

### Examples

```
feat(api): add competency level calculation endpoint
fix(ui): correct alignment of skill matrix table headers
refactor(models): extract base competency class
ci: add staging deployment workflow
chore: update FastAPI to 0.111.0
```

### Breaking Changes

Breaking changes must include `BREAKING CHANGE:` in the commit footer or append `!` after the type/scope:

```
feat(api)!: redesign competency evaluation response schema

BREAKING CHANGE: The response payload for /api/v1/evaluations has changed.
The `score` field is now nested under `result.score`.
```

---

## 4. Pull Request Process

### General Rules

- **All changes** reach `main` exclusively through pull requests.
- No direct pushes to `main`.
- Every PR must pass all CI checks before merging.

### PR Template

Every pull request must include the following sections:

```markdown
## Summary
Brief description of what this PR does and why.

## Type of Change
- [ ] New feature (feat)
- [ ] Bug fix (fix)
- [ ] Refactoring (refactor)
- [ ] Documentation (docs)
- [ ] CI/CD (ci)
- [ ] Other (describe)

## Testing
- Describe how the changes were tested.
- List any new or modified tests.

## Checklist
- [ ] Code follows the project style guidelines
- [ ] Self-review of the code has been performed
- [ ] New and existing tests pass locally
- [ ] Database migrations are included (if applicable)
- [ ] Documentation has been updated (if applicable)
- [ ] No secrets or credentials are included
```

### Review Requirements

Solo developer project: **self-review with the full checklist completed** is sufficient. No mandatory reviewer count.

### AI Agent (Claude Code) Merge Authorization

The AI coding agent (Claude Code) is authorized to perform the full PR lifecycle autonomously:

- Create branches, commits, and pull requests
- Squash merge PRs into `main` after CI passes (or when CI is not yet configured)
- Delete merged branches
- Create version tags and GitHub Releases

The agent follows the same merge strategy (squash merge), commit convention (Conventional Commits), and branching rules as a human developer. No additional human approval is required for merging.

### Merge Strategy

| Branch type | Merge method | Rationale |
|---|---|---|
| `feature/*` → `main` | **Squash merge** | Clean, single-commit history on main |
| `fix/*` → `main` | **Squash merge** | Clean, single-commit history on main |
| `docs/*` → `main` | **Squash merge** | Clean, single-commit history on main |

---

## 5. CI/CD Pipeline

The CI/CD pipeline is implemented with **GitHub Actions**.

### Pipeline Stages

```
┌──────────┐    ┌────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   Lint   │───→│ Type Check │───→│   Test   │───→│  Build   │───→│  Deploy  │
└──────────┘    └────────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Trigger Matrix

| Event | Lint | Type Check | Unit Tests | Build | Deploy |
|---|---|---|---|---|---|
| PR opened/updated | Yes | Yes | Yes | Yes | -- |
| Merge to `main` | Yes | Yes | Yes | Yes | Staging |
| Git tag `v*` | -- | -- | -- | -- | Production |

### Stage Details

#### Lint
- **Backend:** Ruff -- code style, import ordering, unused imports, common errors
- **Frontend:** ESLint + Prettier -- code style, formatting
- **Fails fast:** Yes -- subsequent stages are skipped on failure

#### Type Check
- **Backend:** mypy -- strict mode enabled
- **Frontend:** tsc --noEmit -- TypeScript type checking without emitting output
- **Fails fast:** Yes

#### Unit Tests
- **Backend:** pytest -- minimum 80% coverage threshold enforced, coverage report uploaded as artifact
- **Frontend:** vitest -- unit tests for calculations and logic
- **Reports:** Coverage reports uploaded as artifacts

#### Build
- **Action:** Build Docker images for backend and frontend
- **Tags:** `sha-{commit}`, `latest` (for main), `v{version}` (for tags)
- **Registry:** Yandex Container Registry

#### Deploy Staging
- **Trigger:** Automatically on merge to `main`
- **Target:** Yandex Cloud VM via docker-compose
- **Method:** Pull latest images, restart services

#### Deploy Production
- **Trigger:** On git tag `v*`
- **Target:** Yandex Cloud VM via docker-compose
- **Method:** Pull tagged images, restart services
- **Post-deploy:** Create a GitHub Release from the tag

### Service Containers in CI

- `postgres:16` -- for migration and integration tests
- `redis:7` -- for cache and task queue tests

### Workflow Files

```
.github/
  workflows/
    ci.yml          # Lint + type check + tests + build (on PRs and merge to main)
    deploy.yml      # Deploy to staging (on merge to main) and production (on tag v*)
```

---

## 6. Environments

| Environment | Source | Trigger | URL | Purpose |
|---|---|---|---|---|
| **Development** | Local machine | Manual | `localhost` | Developer workstation |
| **Staging** | `main` branch | Auto on merge to `main` | Yandex Cloud VM (staging) | Integration testing, QA |
| **Production** | `main` branch (tagged) | On git tag `v*` | Yandex Cloud VM (prod) | Live application |

### Development (Local)

- Run via **Docker Compose**: `docker compose up`
- Hot-reload enabled for backend and frontend
- Local database with seed data
- All services run in containers for environment parity

### Staging

- Deployed to Yandex Cloud VM from the `main` branch on every merge
- Uses a staging database (separate from production)
- Mirrors production configuration as closely as possible
- Used for final QA before tagging a release

### Production

- Deployed to Yandex Cloud VM on git tag `v*`
- Production database with real data
- Monitoring and alerting enabled
- Access restricted and audited

### Infrastructure Note

Initially, staging and production can share a single Yandex Cloud VM with separate docker-compose projects and isolated databases. As the project grows, they can be split to separate VMs.

---

## 7. Release Process

Simplified for a solo developer project.

### Step-by-step

1. **Ensure `main` is stable** -- CI is green, staging has been tested.

2. **Create and push a version tag**:
   ```bash
   git checkout main
   git pull origin main
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

3. **CI deploys to production** automatically on the `v*` tag.

4. **Create a GitHub Release** from the tag, including:
   - Release title: `v1.2.0`
   - Release notes / changelog excerpt
   - Any relevant migration instructions

---

## 8. Hotfix Process

Hotfixes follow the same flow as regular fixes. There is no separate hotfix branch type.

### Step-by-step

1. **Create a fix branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b fix/US-XXX-short-desc
   ```

2. **Apply the fix** and commit using conventional commits:
   ```bash
   git commit -m "fix(api): correct null pointer in evaluation endpoint"
   ```

3. **Push the branch** and open a PR to `main`:
   ```bash
   git push origin fix/US-XXX-short-desc
   ```

4. **Ensure CI passes**, complete the self-review checklist, and squash merge to `main`.

5. **Tag a new patch version** on `main`:
   ```bash
   git checkout main
   git pull origin main
   git tag -a v1.2.1 -m "Hotfix v1.2.1"
   git push origin v1.2.1
   ```

6. **CI deploys to production** automatically. Create a GitHub Release from the tag.

7. **Delete the fix branch**:
   ```bash
   git branch -d fix/US-XXX-short-desc
   git push origin --delete fix/US-XXX-short-desc
   ```

---

## 9. Database Migrations

### Tools

- **Alembic** is used for all database schema migrations.
- Migration scripts live in `alembic/versions/`.

### Rules

1. **Every schema change** must have a corresponding Alembic migration.
2. **Migrations are reviewed as part of the PR** -- never applied without review.
3. **Each migration must include both `upgrade()` and `downgrade()`** functions.
4. **Naming convention:** Alembic auto-generates a revision ID. The migration message must be descriptive:
   ```bash
   alembic revision --autogenerate -m "add competency_level column to employees"
   ```
5. **Testing:** Migrations are tested in CI against a clean database (upgrade from scratch) and against the current schema (incremental upgrade).
6. **Production rollback plan:** Every PR that includes a migration must document the rollback procedure in the PR description. This includes:
   - The Alembic downgrade command
   - Any data considerations (e.g., data loss on column removal)
   - Whether the migration is reversible or destructive

### Migration Deployment Order

For an MVP with 10-50 users, brief downtime during deployments is acceptable. The general approach:

1. **Run migrations before deploying new application code** if the new code depends on schema changes.
2. **Deploy new application code before running migrations** if the migration removes columns or tables that old code depends on.

---

## 10. Rollback Strategy

### Application Rollback

If a production deployment introduces a critical issue:

1. **Identify the previous stable image tag** (e.g., `v1.1.0` or a specific commit SHA).
2. **Redeploy the previous container image**:
   ```bash
   # Example: revert to previous version on Yandex Cloud VM
   docker pull cr.yandex/<registry-id>/matrix-app:v1.1.0
   # Update docker-compose to use the previous tag and restart
   docker compose up -d
   ```
3. **Verify** the application is functioning correctly on the rolled-back version.
4. **Investigate** the root cause and create a `fix/*` branch.

### Database Rollback

If the issue is caused by a database migration:

1. **Run Alembic downgrade** to the previous revision:
   ```bash
   alembic downgrade -1    # Downgrade one revision
   # or
   alembic downgrade <revision_id>  # Downgrade to a specific revision
   ```
2. **Verify** data integrity after the downgrade.
3. **Redeploy** the previous application version if needed.

### Rollback Decision Matrix

| Scenario | Action |
|---|---|
| Application bug, no migration involved | Redeploy previous container image |
| Application bug + reversible migration | Alembic downgrade + redeploy previous image |
| Application bug + irreversible migration | Assess data impact, consider forward-fix via `fix/*` branch |
| Performance degradation | Redeploy previous image, investigate |

### Rollback SLA

- **Detection:** Monitoring and alerting should detect issues within 5 minutes.
- **Decision:** Rollback decision should be made within 15 minutes of detection.
- **Execution:** Rollback should be completed within 30 minutes of the decision.

---

## Summary of Key Policies

| Policy | Value |
|---|---|
| Branching model | GitHub Flow |
| Production branch | `main` |
| Feature branches | `feature/*`, `fix/*`, `docs/*` → PR to `main` |
| Versioning | Semantic Versioning (MAJOR.MINOR.PATCH) |
| Commit format | Conventional Commits |
| Merge strategy | Squash merge (all branch types) |
| Review process | Self-review with full checklist (solo developer) |
| AI agent merge | Claude Code authorized to merge autonomously |
| CI stages | Lint, Type Check, Test, Build, Deploy |
| Staging deploy | Auto on merge to `main` |
| Production deploy | On git tag `v*` |
| Hosting | Yandex Cloud |
| Migration tool | Alembic |
| Rollback method | Previous container image + Alembic downgrade |
