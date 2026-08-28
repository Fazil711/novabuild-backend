from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.schemas import PromptRequest, AppPlan
from app.services.plan_engine import generate_plan, generate_plan_stream

router = APIRouter(tags=["plan"])


@router.post("/plan", response_model=AppPlan)
async def create_plan(req: PromptRequest):
    try:
        return await generate_plan(req.prompt)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan/stream")
async def create_plan_stream(req: PromptRequest):
    return StreamingResponse(
        generate_plan_stream(req.prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/plan/stream")
async def create_plan_stream_get(prompt: str = Query(..., min_length=1)):
    return StreamingResponse(
        generate_plan_stream(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )