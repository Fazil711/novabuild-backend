import os
import json
from typing import Optional, List, Dict, Any
from app.schemas import AppPlan
from app.services.code_generator import GENERATED_ROOT
import shutil
import datetime

META_FILENAME = "meta.json"
PROMPTS_FILENAME = "prompts.json"
VERSIONS_DIRNAME = "versions"


def _project_dir(project_id: str) -> str:
    return os.path.join(GENERATED_ROOT, project_id)


def _read_file_safe(path: str) -> str:
    """Read file with utf-8 decoding and graceful fallback for Windows-1252/cp1252."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        try:
            with open(path, "r", encoding="latin-1", errors="replace") as f:
                return f.read()
        except Exception:
            return ""


def _load_json(path: str, default: Any) -> Any:
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
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


def bump_version(project_id: str, user_id: Optional[str] = None) -> int:
    project_dir = _project_dir(project_id)
    meta_path = os.path.join(project_dir, META_FILENAME)
    meta = _load_json(meta_path, {"current_version": 0})
    meta["current_version"] = meta.get("current_version", 0) + 1
    if user_id:
        meta["user_id"] = user_id
    if "created_at" not in meta:
        meta["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    os.makedirs(project_dir, exist_ok=True)
    _save_json(meta_path, meta)
    return meta["current_version"]


def append_prompt_history(project_id: str, prompt: str, version: int, operations: List[dict]):
    path = os.path.join(_project_dir(project_id), PROMPTS_FILENAME)
    history = _load_json(path, [])
    history.append({
        "version": version,
        "prompt": prompt,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operations": operations,
    })
    _save_json(path, history)


def get_prompt_history(project_id: str) -> List[dict]:
    return _load_json(os.path.join(_project_dir(project_id), PROMPTS_FILENAME), [])


def list_versions(project_id: str) -> List[int]:
    versions_dir = os.path.join(_project_dir(project_id), VERSIONS_DIRNAME)
    versions = [get_current_version(project_id)]
    if os.path.isdir(versions_dir):
        for name in os.listdir(versions_dir):
            if name.startswith("v") and name[1:].isdigit():
                versions.append(int(name[1:]))
    return sorted(set(versions))


def list_projects(user_id: Optional[str] = None) -> List[dict]:
    if not os.path.exists(GENERATED_ROOT):
        return []

    summaries = []
    for project_id in os.listdir(GENERATED_ROOT):
        project_dir = os.path.join(GENERATED_ROOT, project_id)
        plan_path = os.path.join(project_dir, "plan.json")
        meta_path = os.path.join(project_dir, META_FILENAME)

        if not os.path.isfile(plan_path):
            continue

        meta = _load_json(meta_path, {})
        if user_id and meta.get("user_id") and meta.get("user_id") != user_id:
            continue

        plan_data = _load_json(plan_path, {})
        files = _list_all_files(project_dir)

        summaries.append({
            "project_id": project_id,
            "app_name": plan_data.get("app_name", "unknown"),
            "type": plan_data.get("type", "unknown"),
            "user_id": meta.get("user_id"),
            "created_files": files,
            "version": meta.get("current_version", 1),
            "updated_at": meta.get("updated_at"),
        })

    return summaries


def get_project(project_id: str) -> Optional[dict]:
    project_dir = os.path.join(GENERATED_ROOT, project_id)
    plan_path = os.path.join(project_dir, "plan.json")
    meta_path = os.path.join(project_dir, META_FILENAME)

    if not os.path.isfile(plan_path):
        return None

    plan_data = _load_json(plan_path, {})
    
    # Gracefully normalize older plan formats if needed
    try:
        from app.services.plan_engine import _normalize_plan
        plan_data = _normalize_plan(plan_data)
        plan = AppPlan(**plan_data)
    except Exception:
        plan = AppPlan(
            app_name=plan_data.get("app_name", "App"),
            type=plan_data.get("type", "saas"),
            description=plan_data.get("description", ""),
            entities=plan_data.get("entities", [])
        )

    meta = _load_json(meta_path, {})

    files = {}
    for rel_path in _list_all_files(project_dir):
        full_path = os.path.join(project_dir, rel_path)
        files[rel_path] = _read_file_safe(full_path)

    return {
        "project_id": project_id,
        "plan": plan,
        "user_id": meta.get("user_id"),
        "version": meta.get("current_version", 1),
        "files": files,
    }


def get_project_file(project_id: str, file_path: str) -> Optional[str]:
    full_path = os.path.join(GENERATED_ROOT, project_id, file_path)

    # Guard against path traversal (../../etc)
    base = os.path.realpath(os.path.join(GENERATED_ROOT, project_id))
    target = os.path.realpath(full_path)
    if not target.startswith(base):
        return None

    if not os.path.isfile(target):
        return None

    return _read_file_safe(target)


def _list_all_files(project_dir: str) -> List[str]:
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