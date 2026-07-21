import uuid
from fastapi import APIRouter, HTTPException
from app.schemas import BuildRequest
from app.services.code_generator import generate_project_files
from app.services import project_store

router = APIRouter()


@router.post("/build")
async def build_project(req: BuildRequest):
    try:
        project_id = str(uuid.uuid4())
        result = generate_project_files(req.plan, project_id)
        result["version"] = project_store.bump_version(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))