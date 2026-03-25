# ADR-001: Архитектурные и реализационные решения

**Статус:** Утверждено
**Дата:** 2026-03-24
**Контекст:** Решения приняты перед началом реализации для устранения противоречий в документации и закрытия слепых пятен

---

## Блок 1: Аутентификация и роли

### Q1. Модель ролей — 6 ролей
- `admin` — полный доступ ко всей системе
- `head` — руководитель управления, **информационный доступ**: видит все 5 отделов (read-only), не оценивает, не калибрует. Может управлять каталогом компетенций и создавать кампании
- `department_head` — руководитель отдела, **оценивает сотрудников своего отдела** (вес 0.35), проводит калибровку, редактирует target profiles, создаёт кампании для своего отдела
- `team_lead` — оценивает свою команду, видит peer-оценки своего отдела
- `hr` — видит все персональные данные, экспорт отчётов, не может редактировать IDP
- `employee` — видит только свои данные, агрегированные оценки

### Q2. Bootstrap — CLI-команда `create-superuser`
Первый пользователь создаётся через CLI (аналогично Django). Эндпоинт публичной регистрации недоступен для bootstrap.

### Q3. Регистрация — свободная с подтверждением Admin
Сотрудники могут зарегистрироваться, но аккаунт неактивен (`is_active=false`) до подтверждения Admin/HR.

### Q4. Access token TTL — 30 минут
Приоритет удобства пользователя. Конфигурируется через `ACCESS_TOKEN_EXPIRE_MINUTES`.

### Q5. Хранение токенов — access в памяти, refresh в httpOnly cookie
При обновлении страницы — silent refresh через `POST /auth/refresh`. CSRF-защита для `/auth/refresh` через SameSite cookie.

### Q6. Сброс пароля — через Telegram-бот
В MVP сброс пароля через Telegram (подтверждение личности через привязанный chat_id). Не требует SMTP.

### Q7. Блокировка аккаунта — Redis-счётчик, 5 попыток, 15 минут
Redis-ключ `login_attempts:{email}` с TTL 15 мин. После 5 неудачных попыток — ответ 429. Автоматическая разблокировка по TTL.

---

## Блок 2: Оценка 360°

### Q8. Веса по умолчанию
Department Head 0.35, TL 0.30, Self 0.20, Peers 0.15. Настраиваемые per-campaign. Head **не оценивает** — роль информационная. **Appendix B tech-spec — ошибка, исправлена.**

### Q9. Метод агрегации — только взвешенное среднее
Среднее арифметическое и медиана не реализуются. Одна формула: `final = dept_head×w_dept_head + tl×w_tl + self×w_self + peer_avg×w_peer`. Поле `aggregation_method` не добавляется в схему. При отсутствии источника — его вес перераспределяется пропорционально оставшимся (см. Q55).

### Q10. Выбор peer-оценщиков — при активации кампании
У сотрудника есть окно (3 дня) на выбор peers после активации кампании. Min 1, max 5.

### Q11. Кросс-отдельная peer-оценка — допустима
Сотрудник может выбрать peer из любого отдела.

### Q12. Перевод сотрудника во время кампании
Текущие незавершённые оценки аннулируются. Новые оценщики назначаются из нового отдела. Оценка по target profile нового отдела.

### Q13. Калибровочная сессия — department_head
Department Head видит флаги (spread >= 2), может скорректировать финальный балл с комментарием. Head видит флаги **информационно** (read-only), не участвует в калибровке.

### Q14. Действия в фазе калибровки — оба варианта
Корректировка aggregated_score (с обязательным комментарием) И возврат оценки конкретному оценщику на пересмотр.

### Q15. Планировщик задач — Celery + Redis
Celery worker + Celery beat для: дедлайнов кампаний, автопродления, напоминаний, проверки IDP-целей. Redis как брокер (уже в стеке).

### Q16. Незавершённые оценки к дедлайну
Автопродление на 2 недели. После повторного дедлайна — незавершённые оценки игнорируются, вес перераспределяется.

### Q17. Видимость оценок для сотрудника — только агрегат
Сотрудник видит только итоговый балл по каждой компетенции. Без разбивки по источникам (self/peer/TL/head).

---

## Блок 3: Компетенции и каталог

### Q18. Управление каталогом — Admin + Head + Department Heads
Admin: полный доступ. Head: полный доступ. Department Heads: CRUD для компетенций своего отдела.

### Q19. Версионирование компетенций — через audit_log
Оценки привязаны к числовому баллу (0-4). При изменении описания уровня — запись в audit_log. Оценки не версионируются.

### Q20. Деактивация компетенции — выбор Admin
При деактивации Admin выбирает: архивировать (`is_archived=true`, сохраняется в истории) или мигрировать оценки на другую компетенцию.

### Q21. Компетенции в target profile — рекомендация 15-20, без жёсткого лимита
Радар-чарт показывает top-N или группировку по категориям.

### Q22. `is_common` — обязательная для всех сотрудников
`is_common=true` означает: компетенция обязательна для всех сотрудников (soft skills, ITIL).

### Q23. Уровни владения — строго 5, описания per-competency
5 уровней (0-4): None, Novice, Basic, Advanced, Expert. Названия уровней стандартные, но **описания критериев задаются для каждой компетенции** через таблицу `competency_level_criteria`. Это позволяет определить, что значит "Advanced" для Kubernetes vs "Advanced" для коммуникации.

---

## Блок 4: Индивидуальный план развития (IDP)

### Q24. Workflow IDP — двусторонний
Сотрудник предлагает → TL подтверждает (или наоборот). Несогласие → эскалация к Department Head.

### Q25. Автоопределение выполнения цели — с подтверждением TL
Если assessment score >= target_level, цель автоматически помечается "pending_completion" + уведомление TL для ручного подтверждения.

### Q26. Carry-over целей — полуавтоматический
Система предлагает перенос невыполненных целей. TL подтверждает каждую цель.

### Q27. Каталог ресурсов — TL+ свободно, сотрудники через модерацию
TL, Department Head, Head, Admin добавляют ресурсы свободно. Сотрудники — через resource_proposals с модерацией.

### Q28. Привязка ресурсов к уровням — да
Ресурс привязан к competency + target_level (например, "Kubernetes Level 2→3"). Добавить `target_level` в `learning_resources`.

---

## Блок 5: Карьерные треки

### Q29. Карьерные треки — двусторонние по умолчанию
Admin может ограничить конкретные направления (поле `is_active` на career_paths).

### Q30. Порог готовности — строго >= 90.0%
Без округления. 89.99% — не готов. Mandatory competencies — строго 100%.

### Q31. Видимость готовности — после одобрения TL/Head
Информация о готовности к переходу видна сотруднику только после одобрения TL/Head.

### Q32. Минимальный стаж — информационно
Система показывает стаж в текущем отделе, но не блокирует готовность.

---

## Блок 6: Уведомления

### Q33. Telegram Bot — long polling (dev), webhook (prod)

### Q34. Связь Telegram — через /start + код
Пользователь пишет боту `/start <код>` (код генерируется в личном кабинете). Бот сохраняет `chat_id`. Поле `telegram_chat_id` добавляется в таблицу `users`.

### Q35. Email — не в MVP
Только Telegram + in-app. Email-уведомления — в будущих версиях.

### Q36. In-app уведомления — да, в MVP
Таблица `notifications`, polling каждые 30с, badge на иконке. Без WebSocket.

### Q37. Категории уведомлений — все отключаемые
Категории: assessment, idp, career, system. Все отключаемые, кроме критичных от Admin (force_send флаг).

---

## Блок 7: Frontend и UX

### Q38. State management — TanStack Query + Zustand
TanStack Query для серверных данных (кеширование, автообновление). Zustand для клиентского UI-состояния.

### Q39. UI-библиотека — Mantine
Современный, чистый дизайн. Хорошие формы, таблицы, responsive hooks. Средний вес бандла.

### Q40. Черновики оценки — автосохранение на сервере
Автосохранение каждые 30с через API (draft-статус в assessments).

### Q41. UX массовой оценки — три режима на выбор
TL выбирает режим: (A) по сотруднику, (B) матрица, (C) по компетенции. Все три режима доступны.

### Q42. Мобильная адаптивность — Mobile-first

### Q43. Язык интерфейса — только русский

---

## Блок 8: Данные и миграция

### Q44. Seed data — полный + demo
- **Production seed:** 5 отделов + каталог компетенций + target profiles + уровни 0-4
- **Dev/staging seed:** + тестовые пользователи + демо-кампания с оценками
- Реализация: `seed.py` скрипт с флагом `--demo`

### Q45. Миграция из существующих систем — нет
Всё с нуля, нет существующей системы оценки.

### Q46. CSV/Excel-импорт — шаблон для скачивания
Excel-шаблон с фиксированными колонками (ФИО, email, отдел, команда, роль). Скачивание шаблона + загрузка заполненного.

### Q47. Soft delete — гибридный подход
| Сущность | Стратегия |
|----------|-----------|
| users | Soft delete (`is_active`) |
| competencies | Soft delete (`is_archived`) |
| campaigns | Soft delete (через статус `archived`) |
| development_plans | Soft delete (`is_archived`) |
| departments | Запрет удаления (5 preset) |
| teams | Hard delete с проверкой "пуста ли команда" |
| learning_resources | Hard delete с каскадным удалением привязок |
| career_paths | Hard delete |
| career_path_requirements | Hard delete |

---

## Блок 9: Инфраструктура и процесс

### Q48. Docker Compose (dev) — 7 сервисов
postgres + redis + backend + frontend + celery-worker + celery-beat + telegram-bot. В dev telegram-bot — отдельный сервис (long polling). В production переключается на webhook (часть FastAPI).

### Q49. Тестовая стратегия frontend — Vitest + RTL для критичного
Vitest для вычислительных функций. React Testing Library для форм оценки и auth-компонентов. Без e2e в MVP.

### Q50. Порядок Phase 0 — Infrastructure-first
1. Docker Compose + CI/CD + DB schema + Alembic (дни 1-5)
2. Backend API + frontend скелет параллельно (дни 6-10)
3. Auth end-to-end + seed data + стабилизация (дни 11-14)

---

## Блок 10: Уточнения модели оценки

### Q51. Head — информационная роль в оценке
Head (руководитель управления) **не ставит оценки** и **не калибрует**. Head может:
- Просматривать все данные по всем отделам (read-only)
- Создавать кампании, управлять каталогом компетенций, target profiles
- Видеть калибровочные флаги (read-only)

Оценка и калибровка — ответственность Department Head.

### Q52. Assessor types — 4 типа (без head)
`assessor_type_enum`: `self`, `peer`, `team_lead`, `department_head`. Тип `head` удалён из enum. В `aggregated_scores` поле `head_score` переименовано в `dept_head_score`. В `assessment_weights` — `head_weight` → `dept_head_weight`.

### Q53. Формула перераспределения весов при отсутствии источника
Если один из источников оценки отсутствует, его вес распределяется пропорционально оставшимся:

```
remaining_total = sum(weights of present sources)
adjusted_weight[i] = original_weight[i] / remaining_total
```

Пример: Department Head не оценил (w=0.35). Оставшиеся: TL 0.30, Self 0.20, Peers 0.15 (сумма = 0.65).
- TL: 0.30/0.65 ≈ 0.4615
- Self: 0.20/0.65 ≈ 0.3077
- Peers: 0.15/0.65 ≈ 0.2308

Если нет ни одного peer — peer_weight перераспределяется аналогично.

### Q54. Peer selection — таблица `peer_selections`
При активации кампании сотрудник выбирает peers через UI. Данные хранятся в таблице:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | PK |
| campaign_id | UUID | FK → assessment_campaigns |
| assessee_id | UUID | FK → users (кто выбирает) |
| peer_id | UUID | FK → users (выбранный peer) |
| selected_at | TIMESTAMPTZ | Время выбора |

**Constraints**: UNIQUE(campaign_id, assessee_id, peer_id). Min 1, max 5 peers. Окно выбора: 3 дня после активации кампании.

### Q55. Draft оценок — поле `is_draft` в `assessment_scores`
Вместо отдельной таблицы — добавляется `is_draft BOOLEAN NOT NULL DEFAULT true` в `assessment_scores`. При автосохранении (каждые 30с) — `is_draft=true`. При submit — все scores переводятся в `is_draft=false`. Агрегация учитывает только `is_draft=false`.

### Q56. User ↔ Target Profile — автоматически по department + position
Система подбирает target profile для пользователя по совпадению `department_id` + `position`. Если совпадений несколько — используется последний созданный. Если совпадений нет — gap-анализ недоступен, UI показывает "target profile не назначен".

**Unique constraint**: `(department_id, position)` на `target_profiles` для однозначного соответствия.

### Q57. Campaign state machine — полная спецификация
```
draft → active → collecting → calibration → finalized → archived
```
- `draft → active`: ручной переход (POST /campaigns/{id}/activate). Запускает окно выбора peers (3 дня).
- `active → collecting`: автоматически через Celery через 3 дня после активации (окно peers закрыто).
- `collecting → calibration`: автоматически, когда все оценки submitted ИЛИ по дедлайну (+ 2 нед. продление). Celery-задача проверяет каждый час.
- `calibration → finalized`: ручной переход Department Head (POST /campaigns/{id}/finalize). Все флаги должны быть resolved.
- `finalized → archived`: ручной переход Admin (POST /campaigns/{id}/archive).

---

## Блок 11: Инфраструктура и безопасность (новые решения)

### Q58. Branching model — GitHub Flow
**Git Flow отменён.** Используется GitHub Flow:
- `main` — production-ready, protected
- `feature/*`, `fix/*`, `docs/*` — от main, PR в main
- Нет `develop`, `release/*`, `hotfix/*`
- Staging: деплоится из main после мержа
- Production: по git tag на main

### Q59. Hosting — Yandex Cloud
- Compute Instance (VM) с Docker Compose
- Managed PostgreSQL (production)
- Container Registry для Docker-образов
- Object Storage для бэкапов
- Lockbox для секретов (JWT_SECRET, TELEGRAM_BOT_TOKEN, DB credentials)

### Q60. Monorepo structure
```
/
├── .github/workflows/       # CI/CD
├── backend/                  # Python (FastAPI)
│   ├── app/
│   │   ├── api/              # Routers
│   │   ├── core/             # Config, security, dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── tasks/            # Celery tasks
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                 # React (TypeScript)
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml        # Dev environment
├── docker-compose.prod.yml   # Production overrides
├── seed.py
├── CLAUDE.md
└── README.md
```

### Q61. Password policy
- Минимум 8 символов
- Минимум 1 буква и 1 цифра
- Проверка при регистрации и смене пароля
- Пароли хешируются bcrypt (cost factor 12)

### Q62. Token revocation — Redis blacklist
При logout/смене пароля: `jti` (JWT ID) access-токена добавляется в Redis SET `revoked_tokens` с TTL = оставшееся время жизни токена. Middleware проверяет `jti` при каждом запросе.

### Q63. CORS policy
- Dev: `http://localhost:3000`
- Staging/Prod: конкретный домен (env var `CORS_ORIGINS`)
- Credentials: true (для httpOnly cookie)
- Methods: GET, POST, PATCH, PUT, DELETE
- Headers: Content-Type, Authorization

### Q64. CSP headers
```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
connect-src 'self' https://api.telegram.org;
```

### Q65. Staging — в Phase 0
Staging-окружение разворачивается в Phase 0, а не в финальном спринте. Без staging невозможно тестировать деплой и миграции.

### Q66. Backups — в Phase 0
Автоматические бэкапы PostgreSQL (pg_dump) ежедневно, хранение 30 дней в Yandex Object Storage. Cron на сервере или Celery Beat задача.

### Q67. Frontend CI pipeline
GitHub Actions для frontend:
- ESLint + Prettier check
- TypeScript type check (tsc --noEmit)
- Vitest (unit tests)
- Build check (vite build)

### Q68. Celery tasks — спецификация
| Task | Schedule | Description |
|------|----------|-------------|
| `close_peer_selection` | hourly check | Переводит кампанию active→collecting через 3 дня |
| `check_campaign_deadline` | hourly check | Автопродление +2 нед, затем принудительное закрытие |
| `send_deadline_reminders` | daily 10:00 | Напоминания за 3 дня и 1 день до дедлайна |
| `check_idp_goals` | daily | Проверка assessment score >= target_level → pending_completion |
| `mark_stale_assessments` | weekly | Пометка оценок старше 2 лет |
| `daily_pg_backup` | daily 03:00 | pg_dump → Yandex Object Storage |

Retry policy: 3 попытки с exponential backoff (10s, 60s, 300s). Dead letter: логирование в audit_log.

---

## Исправленные противоречия

| # | Противоречие | Решение | Статус |
|---|-------------|---------|--------|
| 1 | Веса Appendix B ≠ остальные документы | Dept Head 0.35, TL 0.30, Self 0.20, Peers 0.15 | Исправлено |
| 2 | Token TTL: PRD 30мин vs tech-spec 15мин (expires_in: 900) | 30 минут (expires_in: 1800) | Исправлено |
| 3 | 5 vs 6 ролей в PRD | 6 ролей, PRD обновлён | Исправлено |
| 4 | Кто создаёт кампании: Admin/TL в US-030 | admin + head + department_head (TL не создаёт) | Исправлено |
| 5 | 3 метода агрегации vs 1 | Только взвешенное среднее | Исправлено |
| 6 | Каталог: admin vs admin+head | Admin + Head (read+write) + Department Heads (свой отдел) | Исправлено |
| 7 | Импорт CSV: admin vs admin+HR | Admin + HR | Исправлено |
| 8 | Self-registration vs manual | Свободная регистрация + подтверждение Admin | Исправлено |
| 9 | US-005: "сброс пароля по email" vs ADR Q6 (Telegram) | Через Telegram-бот | Исправлено |
| 10 | US-118: email-уведомления (Should) vs ADR Q35 (no email in MVP) | Удалено из MVP, перенесено в v1.1 | Исправлено |
| 11 | Roadmap Phase 1: "уровни 1-5" vs остальные "0-4" | 0-4 (5 уровней) | Исправлено |
| 12 | Roadmap Phase 2: "HR создаёт кампанию" | Dept Head создаёт кампанию | Исправлено |
| 13 | refresh_token в JSON body vs httpOnly cookie (ADR Q5) | Только httpOnly cookie, убрать из JSON | Исправлено |
| 14 | competency_level_criteria vs "описания одинаковые" (ADR Q23) | Per-competency описания, таблица остаётся | Исправлено |
| 15 | Backlog stats (Epic SP) не совпадают с содержимым эпиков | Пересчитано | Исправлено |
| 16 | Git Flow vs solo developer workflow | GitHub Flow | Исправлено |
| 17 | Head оценивает vs Head информационный | Head информационный, Dept Head оценивает | Исправлено |
| 18 | Docker Compose 4 сервиса, Celery отсутствует | 7 сервисов (+ celery-worker + celery-beat + telegram-bot) | Исправлено |
| 19 | Staging в Sprint 11 vs нужен с Phase 0 | Staging в Phase 0 | Исправлено |
