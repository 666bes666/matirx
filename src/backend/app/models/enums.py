import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HEAD = "head"
    DEPARTMENT_HEAD = "department_head"
    TEAM_LEAD = "team_lead"
    HR = "hr"
    EMPLOYEE = "employee"


class CompetencyCategoryType(str, enum.Enum):
    HARD_SKILL = "hard_skill"
    SOFT_SKILL = "soft_skill"
    PROCESS = "process"
    DOMAIN = "domain"


class CampaignScope(str, enum.Enum):
    DIVISION = "division"
    DEPARTMENT = "department"
    TEAM = "team"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COLLECTING = "collecting"
    CALIBRATION = "calibration"
    FINALIZED = "finalized"
    ARCHIVED = "archived"


class AssessorType(str, enum.Enum):
    SELF = "self"
    PEER = "peer"
    TEAM_LEAD = "team_lead"
    DEPARTMENT_HEAD = "department_head"


class AssessmentStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class PlanApproval(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GoalStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PENDING_COMPLETION = "pending_completion"
    COMPLETED = "completed"


class ResourceType(str, enum.Enum):
    COURSE = "course"
    ARTICLE = "article"
    VIDEO = "video"
    BOOK = "book"
    OTHER = "other"


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ResourceAction(str, enum.Enum):
    ADD = "add"
    REMOVE = "remove"


class CalibrationAction(str, enum.Enum):
    ADJUST = "adjust"
    RETURN_FOR_REVIEW = "return_for_review"
    CONFIRM = "confirm"


class NotificationCategory(str, enum.Enum):
    ASSESSMENT = "assessment"
    IDP = "idp"
    CAREER = "career"
    SYSTEM = "system"
