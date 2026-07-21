import json
import re
from pydantic import ValidationError
from app.schemas import AppPlan
from app.services.openrouter_client import call_openrouter

SYSTEM_PROMPT = """You convert a user's app idea into a strict JSON plan for a CRUD app generator.

Rules:
- Output ONLY valid JSON. No markdown fences, no preamble, no explanation, no trailing text.
- Max 4 entities. Each entity needs 3-8 fields.
- Field types allowed: text, number, boolean, date, textarea, select.
- Keep scope buildable as a simple CRUD app with auth.

Schema:
{
  "app_name": string,
  "type": "saas" | "dashboard" | "internal",
  "description": string,
  "entities": [
    {
      "name": string (singular, e.g. "Task"),
      "plural": string (e.g. "Tasks"),
      "fields": [
        { "name": string, "type": "text"|"number"|"boolean"|"date"|"textarea"|"select", "required": boolean, "options": string[]? }
      ]
    }
  ],
  "features": string[]
}"""


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

    try:
        return AppPlan(**parsed)
    except ValidationError as e:
        raise ValueError(f"Plan failed schema validation: {e}")