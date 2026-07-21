import os
import json
from app.schemas import AppPlan
from app.services.code_generator import GENERATED_ROOT
import shutil
import datetime

META_FILENAME = "meta.json"
PROMPTS_FILENAME = "prompts.json"
VERSIONS_DIRNAME = "versions"


def _project_dir(project_id: str) -> str:
    return os.path.join(GENERATED_ROOT, project_id)


def _load_json(path, default):
    if not os.path.isfile(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_current_version(project_id: str) -> int:
    meta = _load_json(os.path.join(_project_dir(project_id), META_FILENAME), {"current_version": 0})
    return meta.get("current_version", 0)


def snapshot_current_version(project_id: str) -> int:
    """Archive the current on-disk state into versions/vN before it's overwritten."""
    project_dir = _project_dir(project_id)
    current_version = get_current_version(project_id)

    if current_version > 0:
        dest = os.path.join(project_dir, VERSIONS_DIRNAME, f"v{current_version}")
        if not os.path.exists(dest):
            for rel in _list_all_files(project_dir):
                src = os.path.join(project_dir, rel)
                dst = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)

    return current_version


def bump_version(project_id: str) -> int:
    project_dir = _project_dir(project_id)
    meta_path = os.path.join(project_dir, META_FILENAME)
    meta = _load_json(meta_path, {"current_version": 0})
    meta["current_version"] = meta.get("current_version", 0) + 1
    os.makedirs(project_dir, exist_ok=True)
    _save_json(meta_path, meta)
    return meta["current_version"]


def append_prompt_history(project_id: str, prompt: str, version: int, operations: list[dict]):
    path = os.path.join(_project_dir(project_id), PROMPTS_FILENAME)
    history = _load_json(path, [])
    history.append({
        "version": version,
        "prompt": prompt,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "operations": operations,
    })
    _save_json(path, history)


def get_prompt_history(project_id: str) -> list[dict]:
    return _load_json(os.path.join(_project_dir(project_id), PROMPTS_FILENAME), [])


def list_versions(project_id: str) -> list[int]:
    versions_dir = os.path.join(_project_dir(project_id), VERSIONS_DIRNAME)
    versions = [get_current_version(project_id)]
    if os.path.isdir(versions_dir):
        for name in os.listdir(versions_dir):
            if name.startswith("v") and name[1:].isdigit():
                versions.append(int(name[1:]))
    return sorted(set(versions))


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
    for root, dirs, filenames in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d != VERSIONS_DIRNAME]
        for name in filenames:
            if root == project_dir and name in (META_FILENAME, PROMPTS_FILENAME):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, project_dir)
            rel_files.append(rel.replace("\\", "/"))
    return sorted(rel_files)