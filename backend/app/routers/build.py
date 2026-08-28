import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.schemas import BuildRequest
from app.services.code_generator import generate_project_files
from app.services import project_store
from app.dependencies import get_optional_user

router = APIRouter(tags=["build"])


@router.post("/build")
async def build_project(req: BuildRequest, user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    try:
        project_id = str(uuid.uuid4())
        result = generate_project_files(req.plan, project_id)
        user_id = user["id"] if user else None
        result["version"] = project_store.bump_version(project_id, user_id=user_id)
        if user_id:
            result["user_id"] = user_id
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))