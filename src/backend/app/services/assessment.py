import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import (
    AggregatedScore,
    Assessment,
    AssessmentCampaign,
    AssessmentScore,
    AssessmentWeight,
    PeerSelection,
)
from app.models.enums import AssessmentStatus, AssessorType, CampaignStatus
from app.models.user import User
from app.schemas.assessment import AssessmentCreate, AssessmentScoreSubmit, CampaignCreate


class AssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_campaigns(
        self, current_user: User, status: CampaignStatus | None
    ) -> list[AssessmentCampaign]:
        stmt = select(AssessmentCampaign).order_by(AssessmentCampaign.created_at.desc())
        if status is not None:
            stmt = stmt.where(AssessmentCampaign.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_campaign(self, campaign_id: uuid.UUID) -> AssessmentCampaign:
        result = await self.db.execute(
            select(AssessmentCampaign).where(AssessmentCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if campaign is None:
            raise ValueError("not_found")
        return campaign

    async def create_campaign(
        self, data: CampaignCreate, current_user: User
    ) -> AssessmentCampaign:
        if data.end_date <= data.start_date:
            raise ValueError("invalid_dates")
        campaign = AssessmentCampaign(
            name=data.name,
            description=data.description,
            scope=data.scope,
            department_id=data.department_id,
            team_id=data.team_id,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=current_user.id,
        )
        self.db.add(campaign)
        await self.db.flush()
        return await self.get_campaign(campaign.id)

    async def create_assessment(
        self, data: AssessmentCreate, current_user: User
    ) -> Assessment:
        campaign = await self.get_campaign(data.campaign_id)
        if campaign is None:
            raise ValueError("not_found")
        existing = await self.db.execute(
            select(Assessment).where(
                Assessment.campaign_id == data.campaign_id,
                Assessment.assessee_id == data.assessee_id,
                Assessment.assessor_id == current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("duplicate")
        assessment = Assessment(
            campaign_id=data.campaign_id,
            assessee_id=data.assessee_id,
            assessor_id=current_user.id,
            assessor_type=data.assessor_type,
        )
        self.db.add(assessment)
        await self.db.flush()
        return await self.get_assessment(assessment.id)

    async def submit_scores(
        self, assessment_id: uuid.UUID, data: AssessmentScoreSubmit
    ) -> Assessment:
        assessment = await self.get_assessment(assessment_id)
        for score_input in data.scores:
            existing = await self.db.execute(
                select(AssessmentScore).where(
                    AssessmentScore.assessment_id == assessment_id,
                    AssessmentScore.competency_id == score_input.competency_id,
                )
            )
            score_obj = existing.scalar_one_or_none()
            if score_obj is None:
                score_obj = AssessmentScore(
                    assessment_id=assessment_id,
                    competency_id=score_input.competency_id,
                    score=score_input.score,
                    comment=score_input.comment,
                    is_draft=data.is_draft,
                )
                self.db.add(score_obj)
            else:
                score_obj.score = score_input.score
                score_obj.comment = score_input.comment
                score_obj.is_draft = data.is_draft
        if not data.is_draft:
            assessment.status = AssessmentStatus.COMPLETED
            assessment.completed_at = datetime.now(UTC)
        await self.db.flush()
        result = await self.db.execute(
            select(Assessment)
            .options(
                selectinload(Assessment.assessee),
                selectinload(Assessment.assessor),
                selectinload(Assessment.scores),
            )
            .where(Assessment.id == assessment_id)
            .execution_options(populate_existing=True)
        )
        assessment = result.scalar_one_or_none()
        if assessment is None:
            raise ValueError("not_found")
        return assessment

    async def get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        result = await self.db.execute(
            select(Assessment)
            .options(
                selectinload(Assessment.assessee),
                selectinload(Assessment.assessor),
                selectinload(Assessment.scores),
            )
            .where(Assessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment is None:
            raise ValueError("not_found")
        return assessment

    async def list_assessments(
        self,
        current_user: User,
        campaign_id: uuid.UUID | None,
        assessee_id: uuid.UUID | None,
    ) -> list[Assessment]:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.assessee),
                selectinload(Assessment.assessor),
                selectinload(Assessment.scores),
            )
            .order_by(Assessment.created_at.desc())
        )
        if campaign_id is not None:
            stmt = stmt.where(Assessment.campaign_id == campaign_id)
        if assessee_id is not None:
            stmt = stmt.where(Assessment.assessee_id == assessee_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def activate_campaign(self, campaign_id: uuid.UUID) -> AssessmentCampaign:
        campaign = await self.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError("invalid_transition")
        campaign.status = CampaignStatus.ACTIVE
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def close_campaign(self, campaign_id: uuid.UUID) -> AssessmentCampaign:
        campaign = await self.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.ACTIVE, CampaignStatus.COLLECTING):
            raise ValueError("invalid_transition")
        campaign.status = CampaignStatus.CALIBRATION
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def finalize_campaign(self, campaign_id: uuid.UUID) -> AssessmentCampaign:
        campaign = await self.get_campaign(campaign_id)
        allowed = (CampaignStatus.CALIBRATION, CampaignStatus.COLLECTING, CampaignStatus.ACTIVE)
        if campaign.status not in allowed:
            raise ValueError("invalid_transition")
        await self.compute_aggregated_scores(campaign_id)
        campaign.status = CampaignStatus.FINALIZED
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def archive_campaign(self, campaign_id: uuid.UUID) -> AssessmentCampaign:
        campaign = await self.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.FINALIZED:
            raise ValueError("invalid_transition")
        campaign.status = CampaignStatus.ARCHIVED
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def get_campaign_progress(self, campaign_id: uuid.UUID) -> dict:
        await self.get_campaign(campaign_id)
        result = await self.db.execute(
            select(Assessment).where(Assessment.campaign_id == campaign_id)
        )
        assessments = list(result.scalars().all())
        total = len(assessments)
        completed = sum(1 for a in assessments if a.status == AssessmentStatus.COMPLETED)
        pct = round(completed / total * 100, 1) if total > 0 else 0.0
        return {
            "campaign_id": campaign_id,
            "total_assessments": total,
            "completed_assessments": completed,
            "pending_assessments": total - completed,
            "completion_pct": pct,
        }

    async def compute_aggregated_scores(self, campaign_id: uuid.UUID) -> list:
        weights_result = await self.db.execute(
            select(AssessmentWeight).where(AssessmentWeight.campaign_id == campaign_id)
        )
        weight_row = weights_result.scalar_one_or_none()
        if weight_row:
            w_dh = float(weight_row.department_head_weight)
            w_tl = float(weight_row.team_lead_weight)
            w_self = float(weight_row.self_weight)
            w_peer = float(weight_row.peer_weight)
        else:
            w_dh, w_tl, w_self, w_peer = 0.35, 0.30, 0.20, 0.15

        scores_result = await self.db.execute(
            select(AssessmentScore, Assessment)
            .join(Assessment, AssessmentScore.assessment_id == Assessment.id)
            .where(
                Assessment.campaign_id == campaign_id,
                Assessment.status == AssessmentStatus.COMPLETED,
                AssessmentScore.is_draft.is_(False),
            )
        )
        rows = scores_result.all()

        data: dict[tuple, dict[str, list[float]]] = {}
        for score_row, assessment in rows:
            key = (assessment.assessee_id, score_row.competency_id)
            if key not in data:
                data[key] = {t.value: [] for t in AssessorType}
            data[key][assessment.assessor_type.value].append(float(score_row.score))

        def _avg(vals: list[float]) -> float | None:
            return sum(vals) / len(vals) if vals else None

        result_rows = []
        for (user_id, competency_id), type_scores in data.items():
            self_avg = _avg(type_scores["self"])
            tl_avg = _avg(type_scores["team_lead"])
            dh_avg = _avg(type_scores["department_head"])
            peer_avg = _avg(type_scores["peer"])

            sources = []
            if self_avg is not None:
                sources.append((self_avg, w_self))
            if tl_avg is not None:
                sources.append((tl_avg, w_tl))
            if dh_avg is not None:
                sources.append((dh_avg, w_dh))
            if peer_avg is not None:
                sources.append((peer_avg, w_peer))

            if not sources:
                continue

            total_w = sum(w for _, w in sources)
            final = sum(score * w / total_w for score, w in sources)
            final = round(min(4.0, max(0.0, final)), 2)

            existing = await self.db.execute(
                select(AggregatedScore).where(
                    AggregatedScore.campaign_id == campaign_id,
                    AggregatedScore.user_id == user_id,
                    AggregatedScore.competency_id == competency_id,
                )
            )
            agg = existing.scalar_one_or_none()
            if agg is None:
                agg = AggregatedScore(
                    campaign_id=campaign_id,
                    user_id=user_id,
                    competency_id=competency_id,
                    final_score=final,
                    self_score=self_avg,
                    tl_score=tl_avg,
                    dh_score=dh_avg,
                    peer_score=peer_avg,
                )
                self.db.add(agg)
            else:
                agg.final_score = final
                agg.self_score = self_avg
                agg.tl_score = tl_avg
                agg.dh_score = dh_avg
                agg.peer_score = peer_avg
            result_rows.append(agg)

        await self.db.flush()
        return result_rows

    async def get_aggregated_scores(self, campaign_id: uuid.UUID) -> list[AggregatedScore]:
        result = await self.db.execute(
            select(AggregatedScore).where(AggregatedScore.campaign_id == campaign_id)
        )
        return list(result.scalars().all())

    async def set_campaign_weights(self, campaign_id: uuid.UUID, data) -> AssessmentWeight:
        await self.get_campaign(campaign_id)
        existing = await self.db.execute(
            select(AssessmentWeight).where(AssessmentWeight.campaign_id == campaign_id)
        )
        weight = existing.scalar_one_or_none()
        if weight is None:
            weight = AssessmentWeight(
                campaign_id=campaign_id,
                department_head_weight=data.department_head_weight,
                team_lead_weight=data.team_lead_weight,
                self_weight=data.self_weight,
                peer_weight=data.peer_weight,
            )
            self.db.add(weight)
        else:
            weight.department_head_weight = data.department_head_weight
            weight.team_lead_weight = data.team_lead_weight
            weight.self_weight = data.self_weight
            weight.peer_weight = data.peer_weight
        await self.db.flush()
        return weight

    async def set_peers(
        self, campaign_id: uuid.UUID, assessee_id: uuid.UUID, peer_ids: list[uuid.UUID]
    ) -> list[PeerSelection]:
        await self.get_campaign(campaign_id)
        await self.db.execute(
            delete(PeerSelection).where(
                PeerSelection.campaign_id == campaign_id,
                PeerSelection.assessee_id == assessee_id,
            )
        )
        selections = []
        for peer_id in peer_ids:
            sel = PeerSelection(
                campaign_id=campaign_id,
                assessee_id=assessee_id,
                peer_id=peer_id,
            )
            self.db.add(sel)
            selections.append(sel)
        await self.db.flush()
        return selections

    async def get_peers(
        self, campaign_id: uuid.UUID, assessee_id: uuid.UUID
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(PeerSelection).where(
                PeerSelection.campaign_id == campaign_id,
                PeerSelection.assessee_id == assessee_id,
            )
        )
        return [row.peer_id for row in result.scalars().all()]

    async def list_my_tasks(self, current_user: User) -> list[Assessment]:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.assessee),
                selectinload(Assessment.assessor),
                selectinload(Assessment.scores),
            )
            .where(
                Assessment.assessor_id == current_user.id,
                Assessment.status != AssessmentStatus.COMPLETED,
            )
            .order_by(Assessment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
