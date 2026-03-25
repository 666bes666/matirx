# Matrix

**Competency Matrix Platform** — веб-приложение для управления матрицей компетенций сотрудников.

## О проекте

Matrix создан для систематизации оценки компетенций, планирования развития и управления карьерными треками сотрудников IT-подразделений. Изначально разработан для управления сопровождения портала динамической инфраструктуры (частное облако).

### Ключевые возможности

- **Матрица компетенций** — каталог hard/soft skills, процессных и доменных знаний с 5 уровнями владения
- **Оценка 360°** — самооценка + коллеги + тимлид + руководитель
- **Визуализация** — радарные диаграммы, тепловые карты, gap-анализ
- **Карьерные треки** — сквозные пути развития между отделами с анализом готовности
- **Планы развития (IDP)** — индивидуальные цели с привязкой к обучающим ресурсам
- **Отчётность** — экспорт в Excel/PDF, история оценок, динамика роста
- **Уведомления** — Telegram-интеграция

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | React 18+, TypeScript, Vite, Recharts |
| Database | PostgreSQL 16 |
| Cache | Redis |
| Auth | JWT (access + refresh tokens) |
| Notifications | Telegram Bot API |
| CI/CD | GitHub Actions |
| Containers | Docker, Docker Compose |

## Документация

### Бизнес-документация (RU)
- [Product Vision](docs/business/product-vision.md) — видение продукта
- [Market Requirements](docs/business/market-requirements.md) — анализ рынка
- [Business Requirements](docs/business/business-requirements.md) — бизнес-требования
- [Business Plan](docs/business/business-plan.md) — бизнес-план и финансовая модель

### Продуктовая документация (RU)
- [Roadmap](docs/product/roadmap.md) — дорожная карта
- [Product Requirements](docs/product/product-requirements.md) — продуктовые требования (PRD)
- [Product Backlog](docs/product/product-backlog.md) — бэклог продукта

### Техническая документация (EN)
- [Technical Specification](docs/technical/technical-specification.md) — техническое задание
- [Risk Register](docs/technical/risk-register.md) — реестр рисков

### Процессы (EN)
- [Release Policy](docs/process/release-policy.md) — релизная политика и CI/CD

## Quick Start

```bash
# Clone
git clone https://github.com/666bes666/matirx.git
cd matirx

# Local development
docker compose up -d

# Backend (standalone)
cd backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend (standalone)
cd frontend
pnpm install
pnpm dev
```

## Branching Strategy

**GitHub Flow** — simplified for solo developer:

- `main` — production-ready, protected
- `feature/*` — new features
- `fix/*` — bug fixes
- `docs/*` — documentation

All changes via PRs to `main`. See [Release Policy](docs/process/release-policy.md) for details.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
