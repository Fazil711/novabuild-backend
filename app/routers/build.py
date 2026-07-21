import uuid
from fastapi import APIRouter, HTTPException
from app.schemas import BuildRequest
from app.services.code_generator import generate_project_files

router = APIRouter()


@router.post("/build")
async def build_project(req: BuildRequest):
    try:
        project_id = str(uuid.uuid4())
        return generate_project_files(req.plan, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))