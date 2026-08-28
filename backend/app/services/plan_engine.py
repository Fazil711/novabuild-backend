import asyncio
import json
import re
from typing import AsyncGenerator, Dict, Any, List
from pydantic import ValidationError
from app.schemas import AppPlan, NavItem, PageBlueprint, AuthConfig, ProjectDNA
from app.services.openrouter_client import call_openrouter

SYSTEM_PROMPT = """You are the NovaBuild Blueprint Architect. You convert a user's software idea into a complete, structured application blueprint.

Rules:
- Output ONLY valid JSON. No markdown fences, no preamble, no explanation, no trailing text.
- 1 to 5 primary entities. Each entity needs 3-8 fields.
- Field types allowed: text, number, boolean, date, textarea, select.
- Include complete UI page hierarchy, navigation bar configuration, RBAC auth config, and Project DNA.

Schema:
{
  "app_name": "string",
  "type": "saas" | "dashboard" | "internal" | "ecommerce" | "portal",
  "description": "string",
  "project_dna": {
    "business_name": "string",
    "industry": "string",
    "target_users": ["string"],
    "main_workflow": "string",
    "goals": ["string"]
  },
  "entities": [
    {
      "name": "string (singular, e.g. Task)",
      "plural": "string (e.g. Tasks)",
      "fields": [
        { "name": "string", "type": "text"|"number"|"boolean"|"date"|"textarea"|"select", "required": boolean, "options": ["string"]? }
      ]
    }
  ],
  "features": ["string"],
  "pages": [
    {
      "name": "string",
      "path": "string",
      "title": "string",
      "page_type": "dashboard"|"crud_table"|"detail_view"|"form"|"settings",
      "entity_ref": "string (optional matching entity singular name)",
      "description": "string"
    }
  ],
  "navigation": [
    {
      "label": "string",
      "path": "string",
      "icon": "string (Lucide icon name like LayoutDashboard, Users, CheckSquare, Folder, Settings, BarChart3, ShoppingBag)",
      "order": 1,
      "required_role": "string (optional, e.g. admin)"
    }
  ],
  "auth_config": {
    "enabled": true,
    "roles": ["admin", "member", "viewer"],
    "public_signups": true,
    "default_role": "member"
  }
}"""


def _normalize_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure pages, navigation, entities and field types are sanitized and normalized."""
    entities = plan_data.get("entities", [])
    valid_field_types = {"text", "number", "boolean", "date", "textarea", "select"}
    
    # Sanitize entities and field types
    for e in entities:
        for f in e.get("fields", []):
            ft = str(f.get("type", "text")).lower()
            if ft in ("int", "integer", "float", "decimal", "currency", "price"):
                f["type"] = "number"
            elif ft in ("bool",):
                f["type"] = "boolean"
            elif ft in ("datetime", "timestamp", "time"):
                f["type"] = "date"
            elif ft in ("longtext", "description", "body"):
                f["type"] = "textarea"
            elif ft not in valid_field_types:
                f["type"] = "text"
    
    # Auto-generate pages if omitted
    if not plan_data.get("pages"):
        pages = [
            {
                "name": "Dashboard",
                "path": "/",
                "title": f"{plan_data.get('app_name', 'App')} Overview",
                "page_type": "dashboard",
                "description": "Main KPI dashboard and activity feed"
            }
        ]
        for e in entities:
            plural = e.get("plural", e.get("name", "") + "s")
            pages.append({
                "name": plural,
                "path": f"/{plural.lower()}",
                "title": f"{plural} Management",
                "page_type": "crud_table",
                "entity_ref": e.get("name"),
                "description": f"Manage and monitor {plural.lower()}"
            })
        plan_data["pages"] = pages

    # Auto-generate navigation if omitted
    if not plan_data.get("navigation"):
        nav = [
            {"label": "Dashboard", "path": "/", "icon": "LayoutDashboard", "order": 0}
        ]
        icons = ["FolderKanban", "Users", "CheckSquare", "Package", "FileText", "Activity"]
        for idx, e in enumerate(entities):
            plural = e.get("plural", e.get("name", "") + "s")
            icon = icons[idx % len(icons)]
            nav.append({
                "label": plural,
                "path": f"/{plural.lower()}",
                "icon": icon,
                "order": idx + 1
            })
        plan_data["navigation"] = nav

    # Auto-generate auth config if omitted
    if not plan_data.get("auth_config"):
        plan_data["auth_config"] = {
            "enabled": True,
            "roles": ["admin", "member", "viewer"],
            "public_signups": True,
            "default_role": "member"
        }

    return plan_data


async def generate_plan(prompt: str) -> AppPlan:
    raw = await call_openrouter([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON. Raw output: {raw}")

    normalized = _normalize_plan(parsed)

    try:
        return AppPlan(**normalized)
    except ValidationError as e:
        raise ValueError(f"Plan failed schema validation: {e}")


async def generate_plan_stream(prompt: str) -> AsyncGenerator[str, None]:
    """Yield Server-Sent Events (SSE) streaming progress updates and the final blueprint."""
    
    yield f"data: {json.dumps({'step': 1, 'percent': 15, 'message': 'Analyzing software concept & target users...'})}\n\n"
    await asyncio.sleep(0.05)
    
    yield f"data: {json.dumps({'step': 2, 'percent': 35, 'message': 'Architecting relational database entities and attributes...'})}\n\n"
    await asyncio.sleep(0.05)
    
    yield f"data: {json.dumps({'step': 3, 'percent': 60, 'message': 'Designing UI navigation hierarchy and page workflows...'})}\n\n"
    
    # Run LLM call
    try:
        plan = await generate_plan(prompt)
    except Exception as err:
        yield f"data: {json.dumps({'error': str(err)})}\n\n"
        return

    yield f"data: {json.dumps({'step': 4, 'percent': 85, 'message': 'Validating schema integrity and security policies...'})}\n\n"
    await asyncio.sleep(0.05)
    
    yield f"data: {json.dumps({'step': 5, 'percent': 100, 'message': 'Blueprint synthesized successfully!', 'blueprint': plan.model_dump()})}\n\n"