import os
import json
from app.schemas import AppPlan
from app.services.code_generator import GENERATED_ROOT


def list_projects() -> list[dict]:
    if not os.path.exists(GENERATED_ROOT):
        return []

    summaries = []
    for project_id in os.listdir(GENERATED_ROOT):
        project_dir = os.path.join(GENERATED_ROOT, project_id)
        plan_path = os.path.join(project_dir, "plan.json")

        if not os.path.isfile(plan_path):
            continue  # skip anything that isn't a valid generated project

        with open(plan_path, "r") as f:
            plan_data = json.load(f)

        files = _list_all_files(project_dir)

        summaries.append({
            "project_id": project_id,
            "app_name": plan_data.get("app_name", "unknown"),
            "type": plan_data.get("type", "unknown"),
            "created_files": files,
        })

    return summaries


def get_project(project_id: str) -> dict | None:
    project_dir = os.path.join(GENERATED_ROOT, project_id)
    plan_path = os.path.join(project_dir, "plan.json")

    if not os.path.isfile(plan_path):
        return None

    with open(plan_path, "r") as f:
        plan_data = json.load(f)

    plan = AppPlan(**plan_data)

    files = {}
    for rel_path in _list_all_files(project_dir):
        full_path = os.path.join(project_dir, rel_path)
        with open(full_path, "r") as f:
            files[rel_path] = f.read()

    return {"project_id": project_id, "plan": plan, "files": files}


def get_project_file(project_id: str, file_path: str) -> str | None:
    # file_path is relative, e.g. "schema.sql" or "pages/tasks.tsx"
    full_path = os.path.join(GENERATED_ROOT, project_id, file_path)

    # guard against path traversal (../../etc)
    base = os.path.realpath(os.path.join(GENERATED_ROOT, project_id))
    target = os.path.realpath(full_path)
    if not target.startswith(base):
        return None

    if not os.path.isfile(target):
        return None

    with open(target, "r") as f:
        return f.read()


def _list_all_files(project_dir: str) -> list[str]:
    rel_files = []
    for root, _dirs, filenames in os.walk(project_dir):
        for name in filenames:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, project_dir)
            rel_files.append(rel.replace("\\", "/"))  # normalize for Windows
    return sorted(rel_files)