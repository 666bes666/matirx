import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, engine
from app.core.security import hash_password
from app.models.base import Base
from app.models.competency import Competency, CompetencyCategory, ProficiencyLevel
from app.models.department import Department
from app.models.enums import CompetencyCategoryType, UserRole
from app.models.team import Team
from app.models.user import User


DEPARTMENTS = [
    ("Первая линия", "Поддержка пользователей портала, квоты, известные ошибки", 1),
    ("Дежурная смена", "Troubleshooting, Ansible, vCloud Director, инциденты", 2),
    ("Бизнес-логика", "Верификация бизнес-логики портала, управление ресурсами", 3),
    ("Вторая линия (SRE)", "Логи, метрики, код, базы данных, SRE-практики", 4),
    ("Сопровождение Jenkins CDP", "Автоматизация CI/CD через Jenkins", 5),
]

PROFICIENCY_LEVELS = [
    (0, "Нет знаний", "Нет знаний и опыта"),
    (1, "Новичок", "Базовое теоретическое понимание"),
    (2, "Базовый", "Может выполнять задачи с помощью"),
    (3, "Продвинутый", "Работает самостоятельно, решает сложные задачи"),
    (4, "Эксперт", "Глубокая экспертиза, может обучать других"),
]

COMPETENCIES = {
    CompetencyCategoryType.HARD_SKILL: [
        ("Linux администрирование", False),
        ("Сети и протоколы", False),
        ("Kubernetes", False),
        ("Ansible", False),
        ("CI/CD (Jenkins)", False),
        ("Python/Scripting", False),
        ("SQL и базы данных", False),
        ("Мониторинг (Prometheus/Grafana)", False),
        ("vCloud Director", False),
    ],
    CompetencyCategoryType.SOFT_SKILL: [
        ("Коммуникация", True),
        ("Работа в команде", True),
        ("Наставничество", False),
        ("Управление временем", True),
    ],
    CompetencyCategoryType.PROCESS: [
        ("ITIL/ITSM", True),
        ("Incident Management", False),
        ("Change Management", False),
        ("Документирование", True),
    ],
    CompetencyCategoryType.DOMAIN: [
        ("Портал динамической инфраструктуры", False),
        ("Внутренние системы Сбер", False),
    ],
}


async def seed_production(session: AsyncSession) -> None:
    existing = await session.execute(select(Department).limit(1))
    if existing.scalar_one_or_none():
        print("Seed data already exists, skipping production seed")
        return

    departments = {}
    for name, desc, order in DEPARTMENTS:
        dept = Department(name=name, description=desc, sort_order=order)
        session.add(dept)
        departments[name] = dept
    await session.flush()

    for level, name, desc in PROFICIENCY_LEVELS:
        session.add(ProficiencyLevel(level=level, name=name, description=desc))
    await session.flush()

    categories = {}
    for cat_type in CompetencyCategoryType:
        cat = CompetencyCategory(name=cat_type, description=cat_type.value.replace("_", " ").title())
        session.add(cat)
        categories[cat_type] = cat
    await session.flush()

    for cat_type, comps in COMPETENCIES.items():
        for comp_name, is_common in comps:
            session.add(Competency(
                category_id=categories[cat_type].id,
                name=comp_name,
                is_common=is_common,
            ))
    await session.flush()
    await session.commit()
    print("Production seed data created successfully")


async def seed_demo(session: AsyncSession) -> None:
    result = await session.execute(select(Department))
    departments = {d.name: d for d in result.scalars().all()}

    result = await session.execute(select(Team).limit(1))
    if result.scalar_one_or_none():
        print("Demo data already exists, skipping")
        return

    first_line = departments["Первая линия"]
    duty = departments["Дежурная смена"]
    sre = departments["Вторая линия (SRE)"]

    teams_data = [
        (first_line.id, "Команда А"),
        (first_line.id, "Команда Б"),
        (duty.id, "Смена 1"),
        (sre.id, "SRE-команда"),
    ]
    teams = {}
    for dept_id, name in teams_data:
        team = Team(department_id=dept_id, name=name)
        session.add(team)
        teams[name] = team
    await session.flush()

    demo_users = [
        ("admin@matrix.local", "Admin123!", "Системный", "Администратор", UserRole.ADMIN, None, None, True),
        ("head@matrix.local", "Head1234!", "Иван", "Петров", UserRole.HEAD, None, None, True),
        ("dh1@matrix.local", "DeptH123!", "Анна", "Сидорова", UserRole.DEPARTMENT_HEAD, first_line.id, None, True),
        ("dh2@matrix.local", "DeptH123!", "Пётр", "Козлов", UserRole.DEPARTMENT_HEAD, sre.id, None, True),
        ("tl1@matrix.local", "TeamL123!", "Мария", "Иванова", UserRole.TEAM_LEAD, first_line.id, teams["Команда А"].id, True),
        ("tl2@matrix.local", "TeamL123!", "Дмитрий", "Волков", UserRole.TEAM_LEAD, duty.id, teams["Смена 1"].id, True),
        ("hr@matrix.local", "HrPass12!", "Елена", "Кузнецова", UserRole.HR, None, None, True),
        ("emp1@matrix.local", "Emplo123!", "Алексей", "Морозов", UserRole.EMPLOYEE, first_line.id, teams["Команда А"].id, True),
        ("emp2@matrix.local", "Emplo123!", "Ольга", "Новикова", UserRole.EMPLOYEE, first_line.id, teams["Команда А"].id, True),
        ("emp3@matrix.local", "Emplo123!", "Сергей", "Попов", UserRole.EMPLOYEE, duty.id, teams["Смена 1"].id, True),
        ("emp4@matrix.local", "Emplo123!", "Наталья", "Соколова", UserRole.EMPLOYEE, sre.id, teams["SRE-команда"].id, True),
    ]

    for email, pwd, first, last, role, dept_id, team_id, active in demo_users:
        session.add(User(
            email=email,
            password_hash=hash_password(pwd),
            first_name=first,
            last_name=last,
            role=role,
            department_id=dept_id,
            team_id=team_id,
            is_active=active,
        ))

    await session.flush()
    await session.commit()
    print("Demo seed data created successfully")


async def create_superuser(email: str, password: str) -> None:
    async with async_session() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"User {email} already exists")
            return
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name="Admin",
            last_name="Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Superuser {email} created successfully")


async def main():
    demo = "--demo" in sys.argv

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await seed_production(session)
        if demo:
            await seed_demo(session)


if __name__ == "__main__":
    asyncio.run(main())
