from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.schemas import DeployRequest, DeployResult
from app.services import deploy_service

router = APIRouter(prefix="", tags=["deploy"])


@router.post("/projects/{project_id}/deploy", response_model=DeployResult)
async def trigger_project_deploy(project_id: str, req: DeployRequest = DeployRequest()):
    try:
        return await deploy_service.trigger_deployment(project_id, req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/deployments/{deployment_id}/stream")
async def stream_deployment_logs_endpoint(deployment_id: str):
    deployment = deploy_service.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    return StreamingResponse(
        deploy_service.stream_deployment_logs(deployment_id),
        media_type="text/event-stream"
    )


@router.get("/deployments/{deployment_id}", response_model=DeployResult)
def get_deployment_status(deployment_id: str):
    deployment = deploy_service.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment
