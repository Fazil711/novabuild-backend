from fastapi import APIRouter, HTTPException, status
from app.schemas import (
    DiscoveryStartRequest,
    DiscoveryAnswerRequest,
    DiscoverySession,
    AppPlan,
)
from app.services import discovery_engine

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/start", response_model=DiscoverySession)
async def start_discovery_session(req: DiscoveryStartRequest):
    try:
        return await discovery_engine.start_discovery(req.prompt)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{session_id}/answer", response_model=DiscoverySession)
async def submit_discovery_answers(session_id: str, req: DiscoveryAnswerRequest):
    try:
        return await discovery_engine.submit_answers(session_id, req.answers)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{session_id}/synthesize", response_model=AppPlan)
async def synthesize_blueprint_from_discovery(session_id: str):
    try:
        return await discovery_engine.synthesize_discovered_blueprint(session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{session_id}", response_model=DiscoverySession)
def get_discovery_session(session_id: str):
    session = discovery_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session
