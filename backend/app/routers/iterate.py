from fastapi import APIRouter, HTTPException
from app.schemas import IterateRequest, IterateResponse
from app.services.iteration_engine import iterate_project

router = APIRouter()


@router.post("/projects/{project_id}/iterate", response_model=IterateResponse)
async def iterate(project_id: str, req: IterateRequest):
    try:
        return await iterate_project(project_id, req.instruction)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))