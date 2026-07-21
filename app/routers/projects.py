from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.services import project_store

router = APIRouter()


@router.get("/projects")
def list_projects():
    return project_store.list_projects()


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    result = project_store.get_project(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return result


@router.get("/projects/{project_id}/files/{file_path:path}")
def get_project_file(project_id: str, file_path: str):
    content = project_store.get_project_file(project_id, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found in project '{project_id}'")
    return PlainTextResponse(content)

@router.get("/projects/{project_id}/history")
def get_project_history(project_id: str):
    return project_store.get_prompt_history(project_id)


@router.get("/projects/{project_id}/versions")
def get_project_versions(project_id: str):
    return project_store.list_versions(project_id)