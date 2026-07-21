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
    files: dict[str, str]  # filename -> file content