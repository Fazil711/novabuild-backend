from fastapi import APIRouter, HTTPException
from app.schemas import PromptRequest, AppPlan
from app.services.plan_engine import generate_plan

router = APIRouter()


@router.post("/plan", response_model=AppPlan)
async def create_plan(req: PromptRequest):
    try:
        return await generate_plan(req.prompt)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))