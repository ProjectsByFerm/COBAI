from __future__ import annotations

import json

from app.config import PROJECT_ROOT


MODULES_DIR = PROJECT_ROOT / "materials" / "tasks" / "modules"


def list_modules() -> list[dict]:
    modules: list[dict] = []
    for path in sorted(MODULES_DIR.glob("*.json")):
        module = json.loads(path.read_text(encoding="utf-8"))
        modules.append(
            {
                "module_id": module["module_id"],
                "title": module["title"],
                "difficulty": module.get("difficulty", "unknown"),
                "concepts": module.get("concepts", []),
            }
        )
    return modules


def load_module(module_id: str) -> dict:
    path = MODULES_DIR / f"{module_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    available = ", ".join(item["module_id"] for item in list_modules()) or "none"
    raise FileNotFoundError(
        f"Unknown module '{module_id}'. Available modules: {available}"
    )


def load_tutorial_text(module: dict) -> str:
    tutorial_path = PROJECT_ROOT / module["tutorial_file"]
    return tutorial_path.read_text(encoding="utf-8")
