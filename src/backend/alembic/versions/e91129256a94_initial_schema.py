"""initial_schema

Revision ID: e91129256a94
Revises:
Create Date: 2026-03-25 12:20:59.946619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e91129256a94'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('competency_categories',
    sa.Column('name', sa.Enum('hard_skill', 'soft_skill', 'process', 'domain', name='competencycategorytype'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('departments',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('proficiency_levels',
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint('level >= 0 AND level <= 4', name='ck_level_range'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('level')
    )
    op.create_table('career_paths',
    sa.Column('from_department_id', sa.UUID(), nullable=False),
    sa.Column('to_department_id', sa.UUID(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['from_department_id'], ['departments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_department_id'], ['departments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('from_department_id', 'to_department_id', name='uq_career_path')
    )
    op.create_table('competencies',
    sa.Column('category_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_common', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['competency_categories.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('category_id', 'name', name='uq_competency_category_name')
    )
    op.create_table('target_profiles',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=False),
    sa.Column('position', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('department_id', 'position', name='uq_profile_dept_position')
    )
    op.create_table('teams',
    sa.Column('department_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('department_id', 'name', name='uq_team_dept_name')
    )
    op.create_table('career_path_requirements',
    sa.Column('career_path_id', sa.UUID(), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('required_level', sa.Integer(), nullable=False),
    sa.Column('is_mandatory', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint('required_level >= 0 AND required_level <= 4', name='ck_career_req_level_range'),
    sa.ForeignKeyConstraint(['career_path_id'], ['career_paths.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('career_path_id', 'competency_id', name='uq_career_path_competency')
    )
    op.create_table('competency_departments',
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('competency_id', 'department_id')
    )
    op.create_table('competency_level_criteria',
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('criteria_description', sa.Text(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint('level >= 0 AND level <= 4', name='ck_criteria_level_range'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('competency_id', 'level', name='uq_criteria_competency_level')
    )
    op.create_table('learning_resources',
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('url', sa.String(length=2000), nullable=True),
    sa.Column('resource_type', sa.Enum('course', 'article', 'video', 'book', 'other', name='resourcetype'), server_default='other', nullable=False),
    sa.Column('target_level', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('target_profile_competencies',
    sa.Column('target_profile_id', sa.UUID(), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('required_level', sa.Integer(), nullable=False),
    sa.Column('is_mandatory', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint('required_level >= 0 AND required_level <= 4', name='ck_required_level_range'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_profile_id'], ['target_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('target_profile_id', 'competency_id', name='uq_profile_competency')
    )
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('patronymic', sa.String(length=100), nullable=True),
    sa.Column('position', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('admin', 'head', 'department_head', 'team_lead', 'hr', 'employee', name='userrole'), server_default='employee', nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('team_id', sa.UUID(), nullable=True),
    sa.Column('telegram_username', sa.String(length=100), nullable=True),
    sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True),
    sa.Column('notification_preferences', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('hire_date', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('onboarding_completed', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('telegram_chat_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('assessment_campaigns',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('scope', sa.Enum('division', 'department', 'team', name='campaignscope'), server_default='division', nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('team_id', sa.UUID(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('status', sa.Enum('draft', 'active', 'collecting', 'calibration', 'finalized', 'archived', name='campaignstatus'), server_default='draft', nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_date > start_date', name='ck_campaign_dates'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('audit_log',
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('entity_type', sa.String(length=100), nullable=False),
    sa.Column('entity_id', sa.String(length=36), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_created', 'audit_log', ['created_at'], unique=False)
    op.create_index('ix_audit_entity', 'audit_log', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_audit_user', 'audit_log', ['user_id'], unique=False)
    op.create_table('competency_proposals',
    sa.Column('proposed_by', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='proposalstatus'), server_default='pending', nullable=False),
    sa.Column('reviewed_by', sa.UUID(), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['competency_categories.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['proposed_by'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('development_plans',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('draft', 'active', 'completed', name='planstatus'), server_default='draft', nullable=False),
    sa.Column('approval', sa.Enum('pending', 'approved', 'rejected', name='planapproval'), server_default='pending', nullable=False),
    sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('category', sa.Enum('assessment', 'idp', 'career', 'system', name='notificationcategory'), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('telegram_sent', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('force_send', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_table('resource_proposals',
    sa.Column('proposed_by', sa.UUID(), nullable=False),
    sa.Column('resource_id', sa.UUID(), nullable=True),
    sa.Column('action', sa.Enum('add', 'remove', name='resourceaction'), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('url', sa.String(length=2000), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='proposalstatus'), server_default='pending', nullable=False),
    sa.Column('reviewed_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['proposed_by'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('aggregated_scores',
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('final_score', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('self_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('peer_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('tl_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('dh_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['campaign_id'], ['assessment_campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id', 'user_id', 'competency_id', name='uq_aggregated_score')
    )
    op.create_table('assessment_weights',
    sa.Column('campaign_id', sa.UUID(), nullable=True),
    sa.Column('department_head_weight', sa.Numeric(precision=3, scale=2), server_default='0.35', nullable=False),
    sa.Column('team_lead_weight', sa.Numeric(precision=3, scale=2), server_default='0.30', nullable=False),
    sa.Column('self_weight', sa.Numeric(precision=3, scale=2), server_default='0.20', nullable=False),
    sa.Column('peer_weight', sa.Numeric(precision=3, scale=2), server_default='0.15', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['campaign_id'], ['assessment_campaigns.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id')
    )
    op.create_table('assessments',
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('assessee_id', sa.UUID(), nullable=False),
    sa.Column('assessor_id', sa.UUID(), nullable=False),
    sa.Column('assessor_type', sa.Enum('self', 'peer', 'team_lead', 'department_head', name='assessortype'), nullable=False),
    sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', name='assessmentstatus'), server_default='pending', nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['assessee_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['assessor_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['assessment_campaigns.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id', 'assessee_id', 'assessor_id', name='uq_assessment_triple')
    )
    op.create_table('calibration_flags',
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('assessee_id', sa.UUID(), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('max_spread', sa.Integer(), nullable=False),
    sa.Column('resolved', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['assessee_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['assessment_campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('development_goals',
    sa.Column('plan_id', sa.UUID(), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('current_level', sa.Integer(), nullable=False),
    sa.Column('target_level', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('planned', 'in_progress', 'pending_completion', 'completed', name='goalstatus'), server_default='planned', nullable=False),
    sa.Column('deadline', sa.Date(), nullable=True),
    sa.Column('is_mandatory', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('current_level >= 0 AND current_level <= 4', name='ck_goal_current_range'),
    sa.CheckConstraint('target_level > current_level', name='ck_goal_target_gt_current'),
    sa.CheckConstraint('target_level >= 0 AND target_level <= 4', name='ck_goal_target_range'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['plan_id'], ['development_plans.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('peer_selections',
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('assessee_id', sa.UUID(), nullable=False),
    sa.Column('peer_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['assessee_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['campaign_id'], ['assessment_campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['peer_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id', 'assessee_id', 'peer_id', name='uq_peer_selection')
    )
    op.create_table('assessment_scores',
    sa.Column('assessment_id', sa.UUID(), nullable=False),
    sa.Column('competency_id', sa.UUID(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('is_draft', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint('score >= 0 AND score <= 4', name='ck_score_range'),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assessment_id', 'competency_id', name='uq_score_assessment_competency')
    )
    op.create_table('calibration_adjustments',
    sa.Column('flag_id', sa.UUID(), nullable=False),
    sa.Column('adjusted_by', sa.UUID(), nullable=False),
    sa.Column('action', sa.Enum('adjust', 'return_for_review', 'confirm', name='calibrationaction'), nullable=False),
    sa.Column('original_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('adjusted_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default='now()', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['adjusted_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['flag_id'], ['calibration_flags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('goal_resources',
    sa.Column('goal_id', sa.UUID(), nullable=False),
    sa.Column('resource_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['goal_id'], ['development_goals.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('goal_id', 'resource_id')
    )


def downgrade() -> None:
    op.drop_table('goal_resources')
    op.drop_table('calibration_adjustments')
    op.drop_table('assessment_scores')
    op.drop_table('peer_selections')
    op.drop_table('development_goals')
    op.drop_table('calibration_flags')
    op.drop_table('assessments')
    op.drop_table('assessment_weights')
    op.drop_table('aggregated_scores')
    op.drop_table('resource_proposals')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('development_plans')
    op.drop_table('competency_proposals')
    op.drop_index('ix_audit_user', table_name='audit_log')
    op.drop_index('ix_audit_entity', table_name='audit_log')
    op.drop_index('ix_audit_created', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_table('assessment_campaigns')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('target_profile_competencies')
    op.drop_table('learning_resources')
    op.drop_table('competency_level_criteria')
    op.drop_table('competency_departments')
    op.drop_table('career_path_requirements')
    op.drop_table('teams')
    op.drop_table('target_profiles')
    op.drop_table('competencies')
    op.drop_table('career_paths')
    op.drop_table('proficiency_levels')
    op.drop_table('departments')
    op.drop_table('competency_categories')
    op.execute('DROP TYPE IF EXISTS competencycategorytype')
    op.execute('DROP TYPE IF EXISTS resourcetype')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS campaignscope')
    op.execute('DROP TYPE IF EXISTS campaignstatus')
    op.execute('DROP TYPE IF EXISTS proposalstatus')
    op.execute('DROP TYPE IF EXISTS planstatus')
    op.execute('DROP TYPE IF EXISTS planapproval')
    op.execute('DROP TYPE IF EXISTS notificationcategory')
    op.execute('DROP TYPE IF EXISTS resourceaction')
    op.execute('DROP TYPE IF EXISTS assessortype')
    op.execute('DROP TYPE IF EXISTS assessmentstatus')
    op.execute('DROP TYPE IF EXISTS goalstatus')
    op.execute('DROP TYPE IF EXISTS calibrationaction')
