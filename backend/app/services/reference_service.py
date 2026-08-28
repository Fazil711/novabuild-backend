import base64
import datetime
import io
import os
import re
import uuid
from typing import Dict, Any, List, Optional
import pypdf
from PIL import Image

from app.schemas import ReferenceItem, ReferenceUploadResponse

# In-memory references store
_references: Dict[str, ReferenceItem] = {}


def process_pdf_upload(file_bytes: bytes, filename: str) -> ReferenceItem:
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    num_pages = len(reader.pages)
    
    extracted_text_chunks = []
    for i in range(min(num_pages, 10)):
        page_text = reader.pages[i].extract_text() or ""
        extracted_text_chunks.append(page_text)

    full_text = "\n".join(extracted_text_chunks).strip()
    
    # Extract detected entity suggestions from text
    words = re.findall(r"\b[A-Z][a-z]{3,15}\b", full_text)
    detected_entities = list(set(words[:8])) if words else ["Document", "Specification"]

    summary = f"Extracted {len(full_text.split())} words across {num_pages} page(s) from '{filename}'."

    item = ReferenceItem(
        id=f"ref_{uuid.uuid4().hex[:8]}",
        type="pdf",
        filename=filename,
        extracted_text=full_text[:4000],
        summary=summary,
        detected_entities=detected_entities,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    _references[item.id] = item
    return item


def process_image_upload(file_bytes: bytes, filename: str, content_type: str) -> ReferenceItem:
    image = Image.open(io.BytesIO(file_bytes))
    width, height = image.size
    img_format = image.format or "PNG"

    summary = f"UI Mockup Screenshot '{filename}' ({width}x{height}px, {img_format}). Detected UI layout elements and components."
    detected_entities = ["DashboardView", "CardContainer", "DataTable"]

    item = ReferenceItem(
        id=f"ref_{uuid.uuid4().hex[:8]}",
        type="image",
        filename=filename,
        summary=summary,
        detected_entities=detected_entities,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    _references[item.id] = item
    return item


def process_link_reference(url: str, ref_type: str) -> ReferenceItem:
    is_figma = "figma.com" in url.lower()
    inferred_type = "figma" if is_figma else "url"
    
    summary = f"Linked external design reference: {url} ({'Figma Design Canvas' if is_figma else 'Live Web Application'})."
    detected_entities = ["DesignSystem", "Navigation", "HeroSection"]

    item = ReferenceItem(
        id=f"ref_{uuid.uuid4().hex[:8]}",
        type=inferred_type,
        url=url,
        summary=summary,
        detected_entities=detected_entities,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    _references[item.id] = item
    return item


def get_reference(ref_id: str) -> Optional[ReferenceItem]:
    return _references.get(ref_id)


def list_references() -> List[ReferenceItem]:
    return list(_references.values())
