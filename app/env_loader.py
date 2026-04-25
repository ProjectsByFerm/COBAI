from __future__ import annotations

from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "app" / ".env",
)


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip("'").strip('"')
    if not key:
        return None
    return key, value


def load_env_files() -> None:
    for path in DEFAULT_ENV_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(line)
            if not parsed:
                continue
            key, value = parsed
            os.environ.setdefault(key, value)
