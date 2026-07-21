from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class FieldSchema(BaseModel):
    name: str
    type: Literal["text", "number", "boolean", "date", "textarea", "select"]
    required: bool = False
    options: Optional[List[str]] = None


class EntitySchema(BaseModel):
    name: str          # singular, e.g. "Task"
    plural: str        # e.g. "Tasks"
    fields: List[FieldSchema] = Field(..., min_length=1, max_length=8)


class AppPlan(BaseModel):
    app_name: str
    type: Literal["saas", "dashboard", "internal"]
    description: str
    entities: List[EntitySchema] = Field(..., min_length=1, max_length=4)
    features: List[str] = []

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