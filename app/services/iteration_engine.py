import json
import os
import re
from typing import List, Tuple
from pydantic import ValidationError

from app.schemas import AppPlan, EntitySchema, PlanDiffOp, IterateResponse
from app.services.openrouter_client import call_openrouter
from app.services import project_store
from app.services.code_generator import (
    GENERATED_ROOT,
    write_plan_json,
    write_schema_sql,
    write_entity_page,
    remove_entity_page,
)

SYSTEM_PROMPT = """You update an existing app plan based on a user's change request.

You will be given the CURRENT PLAN (JSON) and an INSTRUCTION describing a change.

Output ONLY a JSON object with a single key "operations": a list of operations to apply.
No markdown fences, no preamble, no explanation, no trailing text.

Each operation is one of:
{"op": "add_entity", "entity": <EntitySchema>}
{"op": "remove_entity", "entity_name": "Task"}
{"op": "modify_entity", "entity_name": "Task", "entity": <EntitySchema>}
{"op": "add_feature", "feature": "string"}
{"op": "remove_feature", "feature": "string"}
{"op": "update_meta", "app_name": "string"?, "description": "string"?}

EntitySchema:
{
  "name": string (singular),
  "plural": string,
  "fields": [{ "name": string, "type": "text"|"number"|"boolean"|"date"|"textarea"|"select", "required": boolean, "options": string[]? }]
}

Rules:
- Only include operations necessary to satisfy the instruction.
- Never touch entities or features not implicated by the instruction.
- Total entities after applying all operations must stay between 1 and 4.
- Each entity must keep between 1 and 8 fields.
"""


async def generate_diff(current_plan: AppPlan, instruction: str) -> List[PlanDiffOp]:
    raw = await call_openrouter([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"CURRENT PLAN:\n{current_plan.model_dump_json(indent=2)}\n\n"
            f"INSTRUCTION:\n{instruction}"
        )},
    ])

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON. Raw output: {raw}")

    ops_raw = parsed.get("operations")
    if not isinstance(ops_raw, list) or not ops_raw:
        raise ValueError(f"Model returned no operations. Raw output: {raw}")

    try:
        return [PlanDiffOp(**op) for op in ops_raw]
    except ValidationError as e:
        raise ValueError(f"Diff failed schema validation: {e}")


def apply_diff(current_plan: AppPlan, ops: List[PlanDiffOp]) -> Tuple[AppPlan, List[str], List[str]]:
    """Apply diff operations to a plan.
    Returns (new_plan, touched_entity_plurals, removed_entity_plurals)."""
    entities = {e.name: e for e in current_plan.entities}
    order = [e.name for e in current_plan.entities]
    features = list(current_plan.features)
    app_name = current_plan.app_name
    description = current_plan.description

    touched: List[str] = []
    removed: List[str] = []

    for op in ops:
        if op.op == "add_entity":
            if op.entity is None:
                raise ValueError("add_entity requires 'entity'")
            if op.entity.name in entities:
                raise ValueError(f"Entity '{op.entity.name}' already exists")
            if len(entities) >= 4:
                raise ValueError("Cannot add entity: max 4 entities reached")
            entities[op.entity.name] = op.entity
            order.append(op.entity.name)
            touched.append(op.entity.plural.lower())

        elif op.op == "remove_entity":
            if not op.entity_name or op.entity_name not in entities:
                raise ValueError(f"Cannot remove unknown entity '{op.entity_name}'")
            removed.append(entities[op.entity_name].plural.lower())
            del entities[op.entity_name]
            order.remove(op.entity_name)

        elif op.op == "modify_entity":
            if not op.entity_name or op.entity_name not in entities:
                raise ValueError(f"Cannot modify unknown entity '{op.entity_name}'")
            if op.entity is None:
                raise ValueError("modify_entity requires 'entity'")
            old_entity = entities.pop(op.entity_name)
            old_plural = old_entity.plural.lower()
            new_plural = op.entity.plural.lower()
            if new_plural != old_plural:
                removed.append(old_plural)
            entities[op.entity.name] = op.entity
            order = [op.entity.name if n == op.entity_name else n for n in order]
            touched.append(new_plural)

        elif op.op == "add_feature":
            if op.feature and op.feature not in features:
                features.append(op.feature)

        elif op.op == "remove_feature":
            if op.feature in features:
                features.remove(op.feature)

        elif op.op == "update_meta":
            if op.app_name:
                app_name = op.app_name
            if op.description:
                description = op.description

        else:
            raise ValueError(f"Unknown operation '{op.op}'")

    new_entities = [entities[name] for name in order]
    if not (1 <= len(new_entities) <= 4):
        raise ValueError("Resulting plan must have between 1 and 4 entities")

    new_plan = AppPlan(
        app_name=app_name,
        type=current_plan.type,
        description=description,
        entities=new_entities,
        features=features,
    )
    return new_plan, touched, removed


async def iterate_project(project_id: str, instruction: str) -> IterateResponse:
    project = project_store.get_project(project_id)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found")

    current_plan: AppPlan = project["plan"]

    ops = await generate_diff(current_plan, instruction)
    new_plan, touched, removed = apply_diff(current_plan, ops)

    base_dir = os.path.join(GENERATED_ROOT, project_id)

    project_store.snapshot_current_version(project_id)
    new_version = project_store.bump_version(project_id)

    # plan + schema are cheap and correctness-critical, always refresh in full
    write_plan_json(base_dir, new_plan)
    write_schema_sql(base_dir, new_plan)

    changed_files = ["plan.json", "schema.sql"]
    removed_files: List[str] = []

    entity_by_plural = {e.plural.lower(): e for e in new_plan.entities}

    for plural in set(touched):
        if plural in entity_by_plural:
            changed_files.append(write_entity_page(base_dir, entity_by_plural[plural]))

    for plural in set(removed):
        if plural not in entity_by_plural:
            removed_files.append(remove_entity_page(base_dir, plural))

    project_store.append_prompt_history(
        project_id, instruction, new_version, [op.model_dump() for op in ops]
    )

    return IterateResponse(
        project_id=project_id,
        version=new_version,
        plan=new_plan,
        operations=ops,
        changed_files=changed_files,
        removed_files=removed_files,
    )