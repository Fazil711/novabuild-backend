import io
import os
import zipfile
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse, StreamingResponse
from app.services import project_store
from app.services.code_generator import GENERATED_ROOT
from app.dependencies import get_optional_user

router = APIRouter(tags=["projects"])


@router.get("/projects")
def list_projects(user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    user_id = user["id"] if user else None
    return project_store.list_projects(user_id=user_id)


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


@router.get("/projects/{project_id}/download")
def download_project_zip(project_id: str):
    project_dir = os.path.join(GENERATED_ROOT, project_id)
    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d != "versions"]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_dir)
                zip_file.write(full_path, rel_path)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="novabuild_{project_id}.zip"'}
    )