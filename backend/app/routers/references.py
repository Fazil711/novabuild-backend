from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.schemas import ReferenceItem, ReferenceLinkRequest, ReferenceUploadResponse
from app.services import reference_service

router = APIRouter(prefix="/references", tags=["references"])


@router.post("/upload", response_model=ReferenceUploadResponse)
async def upload_reference_file(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_file"
    content_type = file.content_type or ""
    
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded")

    if filename.lower().endswith(".pdf") or "pdf" in content_type:
        item = reference_service.process_pdf_upload(file_bytes, filename)
    elif any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]) or "image" in content_type:
        item = reference_service.process_image_upload(file_bytes, filename, content_type)
    else:
        # Fallback text/generic
        item = reference_service.process_pdf_upload(file_bytes, filename)

    return ReferenceUploadResponse(
        reference=item,
        message=f"Reference '{filename}' processed and ingested successfully."
    )


@router.post("/link", response_model=ReferenceUploadResponse)
def link_external_reference(req: ReferenceLinkRequest):
    if not req.url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL is required")

    item = reference_service.process_link_reference(req.url, req.type)
    return ReferenceUploadResponse(
        reference=item,
        message="External design reference linked successfully."
    )


@router.get("", response_model=List[ReferenceItem])
def list_all_references():
    return reference_service.list_references()


@router.get("/{ref_id}", response_model=ReferenceItem)
def get_reference_details(ref_id: str):
    item = reference_service.get_reference(ref_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")
    return item
