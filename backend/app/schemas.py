from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ---- User Management & Auth Schemas ----

class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    google_id: Optional[str] = None


# ---- Blueprint & Plan Schemas ----

class NavItem(BaseModel):
    label: str
    path: str
    icon: Optional[str] = "LayoutGrid"
    order: int = 0
    required_role: Optional[str] = None


class PageBlueprint(BaseModel):
    name: str                           # e.g., "Tasks" or "Dashboard"
    path: str                           # e.g., "/tasks" or "/"
    title: str                          # e.g., "Task Management"
    page_type: Literal["dashboard", "crud_table", "detail_view", "form", "settings"] = "crud_table"
    entity_ref: Optional[str] = None    # references EntitySchema.name
    description: Optional[str] = None


class AuthConfig(BaseModel):
    enabled: bool = True
    roles: List[str] = ["admin", "member", "viewer"]
    public_signups: bool = True
    default_role: str = "member"


class ProjectDNA(BaseModel):
    business_name: Optional[str] = None
    industry: Optional[str] = None
    target_users: List[str] = []
    main_workflow: Optional[str] = None
    goals: List[str] = []


class FieldSchema(BaseModel):
    name: str
    type: Literal["text", "number", "boolean", "date", "textarea", "select"]
    required: bool = False
    options: Optional[List[str]] = None


class EntitySchema(BaseModel):
    name: str          # singular, e.g. "Task"
    plural: str        # e.g. "Tasks"
    fields: List[FieldSchema] = Field(..., min_length=1, max_length=20)


class AppPlan(BaseModel):
    app_name: str
    type: str = "saas"
    description: str
    entities: List[EntitySchema] = Field(..., min_length=1, max_length=8)
    features: List[str] = []
    pages: Optional[List[PageBlueprint]] = None
    navigation: Optional[List[NavItem]] = None
    auth_config: Optional[AuthConfig] = None
    project_dna: Optional[ProjectDNA] = None


class PromptRequest(BaseModel):
    prompt: str


class BuildRequest(BaseModel):
    plan: AppPlan

# add to existing schemas.py

class ProjectSummary(BaseModel):
    project_id: str
    app_name: str
    type: str
    created_files: List[str]


class ProjectDetail(BaseModel):
    project_id: str
    plan: AppPlan
    files: dict[str, str]  

# ---- Iteration engine ----

class PlanDiffOp(BaseModel):
    """A single, targeted change to an existing AppPlan.
    Only the fields relevant to `op` are populated."""
    op: Literal[
        "add_entity", "remove_entity", "modify_entity",
        "add_feature", "remove_feature", "update_meta",
    ]
    entity: Optional[EntitySchema] = None       # add_entity / modify_entity
    entity_name: Optional[str] = None           # remove_entity / modify_entity target
    feature: Optional[str] = None               # add_feature / remove_feature
    app_name: Optional[str] = None              # update_meta
    description: Optional[str] = None           # update_meta


class IterateRequest(BaseModel):
    instruction: str


class IterateResponse(BaseModel):
    project_id: str
    version: int
    plan: AppPlan
    operations: List[PlanDiffOp]
    changed_files: List[str]
    removed_files: List[str]


class PromptHistoryEntry(BaseModel):
    version: int
    prompt: str
    timestamp: str
    operations: List[PlanDiffOp] = []


# ---- Conversational Discovery & Confidence Schemas ----

class DiscoveryQuestion(BaseModel):
    id: str
    question: str
    category: Literal["business", "users", "workflow", "data", "features", "design"] = "business"
    type: Literal["text", "single_choice", "multi_choice"] = "text"
    options: Optional[List[str]] = None
    context_hint: Optional[str] = None


class DiscoveryAnswer(BaseModel):
    question_id: str
    answer: str


class DiscoveryStartRequest(BaseModel):
    prompt: str


class DiscoveryAnswerRequest(BaseModel):
    answers: List[DiscoveryAnswer]


class ConfidenceScore(BaseModel):
    score: int                                      # 0 to 100
    summary: str                                    # "Here's what I understood..."
    breakdown: dict[str, int] = {}                  # e.g., {"business": 95, "workflow": 90, "data": 88}
    status: Literal["ready_to_build", "needs_clarification"] = "ready_to_build"
    follow_up_questions: Optional[List[DiscoveryQuestion]] = None


class DiscoverySession(BaseModel):
    session_id: str
    prompt: str
    questions: List[DiscoveryQuestion]
    answers: dict[str, str] = {}
    confidence: Optional[ConfidenceScore] = None
    blueprint: Optional[AppPlan] = None
    created_at: str


# ---- Cloud Deployment Schemas ----

class DeployRequest(BaseModel):
    provider: Literal["vercel", "netlify", "mock"] = "vercel"
    project_name: Optional[str] = None
    auth_token: Optional[str] = None
    env_vars: Optional[dict[str, str]] = None


class DeployLogEntry(BaseModel):
    step: str
    percent: int
    message: str
    status: Literal["building", "ready", "failed"] = "building"
    timestamp: str


class DeployResult(BaseModel):
    deployment_id: str
    project_id: str
    provider: str
    url: str
    status: str
    logs: List[DeployLogEntry] = []
    created_at: str


# ---- Multi-Modal Reference Ingestion Schemas ----

class ReferenceItem(BaseModel):
    id: str
    type: Literal["image", "pdf", "figma", "url"]
    filename: Optional[str] = None
    url: Optional[str] = None
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    detected_entities: List[str] = []
    created_at: str


class ReferenceLinkRequest(BaseModel):
    url: str
    type: Literal["figma", "url"] = "url"


class ReferenceUploadResponse(BaseModel):
    reference: ReferenceItem
    message: str
