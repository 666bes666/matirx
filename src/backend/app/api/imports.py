import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.security import hash_password, validate_password
from app.models.competency import Competency, CompetencyCategory
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/users")
async def import_users(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("admin", "head", "hr")),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Требуется CSV-файл")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    required = {"email", "first_name", "last_name", "password", "role"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"CSV должен содержать колонки: {', '.join(sorted(required))}",
        )

    created = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        email = row.get("email", "").strip().lower()
        if not email:
            errors.append(f"Строка {row_num}: пустой email")
            continue

        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            errors.append(f"Строка {row_num}: email {email} уже занят")
            continue

        password = row.get("password", "").strip()
        if not validate_password(password):
            errors.append(f"Строка {row_num}: пароль не соответствует требованиям")
            continue

        role_str = row.get("role", "employee").strip().lower()
        try:
            role = UserRole(role_str)
        except ValueError:
            errors.append(f"Строка {row_num}: неизвестная роль '{role_str}'")
            continue

        dept_id = None
        dept_name = row.get("department", "").strip()
        if dept_name:
            dept_r = await db.execute(select(Department).where(Department.name == dept_name))
            dept = dept_r.scalar_one_or_none()
            if dept:
                dept_id = dept.id

        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=row.get("first_name", "").strip(),
            last_name=row.get("last_name", "").strip(),
            patronymic=row.get("patronymic", "").strip() or None,
            position=row.get("position", "").strip() or None,
            role=role,
            department_id=dept_id,
            is_active=True,
        )
        db.add(user)
        created += 1

    await db.flush()
    return {"created": created, "errors": errors}


@router.post("/competencies")
async def import_competencies(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("admin", "head")),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Требуется CSV-файл")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    required = {"name", "category"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"CSV должен содержать колонки: {', '.join(sorted(required))}",
        )

    created = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        if not name:
            errors.append(f"Строка {row_num}: пустое название")
            continue

        category_name = row.get("category", "").strip()
        try:
            cat_r = await db.execute(
                select(CompetencyCategory).where(CompetencyCategory.name == category_name)
            )
            category = cat_r.scalar_one_or_none()
        except Exception:
            category = None
        if category is None:
            errors.append(f"Строка {row_num}: категория '{category_name}' не найдена")
            continue

        existing = await db.execute(
            select(Competency).where(
                Competency.name == name, Competency.category_id == category.id
            )
        )
        if existing.scalar_one_or_none() is not None:
            errors.append(f"Строка {row_num}: компетенция '{name}' уже существует")
            continue

        competency = Competency(
            category_id=category.id,
            name=name,
            description=row.get("description", "").strip() or None,
        )
        db.add(competency)
        created += 1

    await db.flush()
    return {"created": created, "errors": errors}
