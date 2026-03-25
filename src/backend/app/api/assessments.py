import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.enums import CampaignStatus
from app.models.user import User
from app.schemas.assessment import (
    AggregatedScoreRead,
    AssessmentCreate,
    AssessmentRead,
    AssessmentScoreSubmit,
    CampaignCreate,
    CampaignProgressRead,
    CampaignRead,
    CampaignWeightsUpdate,
    PeerSetRequest,
)
from app.services.assessment import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "Не найдено"),
    "duplicate": (status.HTTP_409_CONFLICT, "Оценка уже существует"),
    "invalid_dates": (status.HTTP_400_BAD_REQUEST, "Дата окончания должна быть позже даты начала"),
    "invalid_transition": (status.HTTP_409_CONFLICT, "Недопустимый переход статуса"),
}


def _raise(code: str) -> None:
    status_code, detail = ERROR_MAP.get(code, (400, code))
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("/campaigns", response_model=list[CampaignRead])
async def list_campaigns(
    campaign_status: CampaignStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    return await service.list_campaigns(current_user, campaign_status)


@router.post(
    "/campaigns",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = AssessmentService(db)
    try:
        campaign = await service.create_campaign(data, current_user)
    except ValueError as e:
        _raise(str(e))
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    try:
        campaign = await service.get_campaign(campaign_id)
    except ValueError as e:
        _raise(str(e))
    return campaign


@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "team_lead", "department_head")),
):
    service = AssessmentService(db)
    try:
        assessment = await service.create_assessment(data, current_user)
    except ValueError as e:
        _raise(str(e))
    return assessment


@router.get("", response_model=list[AssessmentRead])
async def list_assessments(
    campaign_id: uuid.UUID | None = Query(default=None),
    assessee_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    return await service.list_assessments(current_user, campaign_id, assessee_id)


@router.get("/{assessment_id}", response_model=AssessmentRead)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    try:
        assessment = await service.get_assessment(assessment_id)
    except ValueError as e:
        _raise(str(e))
    return assessment


@router.post("/{assessment_id}/scores", response_model=AssessmentRead)
async def submit_scores(
    assessment_id: uuid.UUID,
    data: AssessmentScoreSubmit,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    try:
        assessment = await service.submit_scores(assessment_id, data)
    except ValueError as e:
        _raise(str(e))
    return assessment


@router.post("/campaigns/{campaign_id}/activate", response_model=CampaignRead)
async def activate_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = AssessmentService(db)
    try:
        return await service.activate_campaign(campaign_id)
    except ValueError as e:
        _raise(str(e))


@router.post("/campaigns/{campaign_id}/close", response_model=CampaignRead)
async def close_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = AssessmentService(db)
    try:
        return await service.close_campaign(campaign_id)
    except ValueError as e:
        _raise(str(e))


@router.post("/campaigns/{campaign_id}/finalize", response_model=CampaignRead)
async def finalize_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = AssessmentService(db)
    try:
        return await service.finalize_campaign(campaign_id)
    except ValueError as e:
        _raise(str(e))


@router.post("/campaigns/{campaign_id}/archive", response_model=CampaignRead)
async def archive_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = AssessmentService(db)
    try:
        return await service.archive_campaign(campaign_id)
    except ValueError as e:
        _raise(str(e))


@router.get("/campaigns/{campaign_id}/progress", response_model=CampaignProgressRead)
async def get_campaign_progress(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    try:
        return await service.get_campaign_progress(campaign_id)
    except ValueError as e:
        _raise(str(e))


@router.get("/campaigns/{campaign_id}/scores", response_model=list[AggregatedScoreRead])
async def get_aggregated_scores(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head", "team_lead", "hr")),
):
    service = AssessmentService(db)
    try:
        return await service.get_aggregated_scores(campaign_id)
    except ValueError as e:
        _raise(str(e))


@router.put("/campaigns/{campaign_id}/weights")
async def set_campaign_weights(
    campaign_id: uuid.UUID,
    data: CampaignWeightsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    service = AssessmentService(db)
    try:
        await service.set_campaign_weights(campaign_id, data)
        return {"ok": True}
    except ValueError as e:
        _raise(str(e))


@router.post("/campaigns/{campaign_id}/peers")
async def set_peers(
    campaign_id: uuid.UUID,
    data: PeerSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    try:
        await service.set_peers(campaign_id, current_user.id, data.peer_ids)
        return {"ok": True}
    except ValueError as e:
        _raise(str(e))


@router.get("/campaigns/{campaign_id}/peers")
async def get_peers(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    try:
        peer_ids = await service.get_peers(campaign_id, current_user.id)
        return [str(p) for p in peer_ids]
    except ValueError as e:
        _raise(str(e))


@router.get("/my-tasks", response_model=list[AssessmentRead])
async def list_my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssessmentService(db)
    return await service.list_my_tasks(current_user)
