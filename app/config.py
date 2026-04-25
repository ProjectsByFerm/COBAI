from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from app.env_loader import load_env_files


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    api_key: str | None = field(repr=False)
    api_base_url: str
    model: str
    reasoning_effort: str | None
    temperature: float | None
    previous_response_id_enabled: bool
    prompt_version: str
    timeout_seconds: int
    max_output_tokens: int
    prompt_path: Path
    raw_data_dir: Path

    @property
    def api_endpoint(self) -> str:
        return f"{self.api_base_url.rstrip('/')}/responses"

    @property
    def ollama_generate_endpoint(self) -> str:
        base_url = self.api_base_url.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        return f"{base_url}/api/generate"


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _optional_float(name: str) -> float | None:
    value = _env(name)
    if value is None:
        return None
    return float(value)


def _bool(name: str, default: bool) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    load_env_files()
    prompt_version = _env("LLM_PROMPT_VERSION", "cobol_coach_v1")

    return Settings(
        api_key=_env("LLM_API_KEY", "ollama"),
        api_base_url=_env("LLM_API_BASE_URL", "http://localhost:11434/v1"),
        model=_env("LLM_MODEL", "qwen2.5-coder:7b"),
        reasoning_effort=_env("LLM_REASONING_EFFORT"),
        temperature=_optional_float("LLM_TEMPERATURE"),
        previous_response_id_enabled=_bool("LLM_PREVIOUS_RESPONSE_ID_ENABLED", False),
        prompt_version=prompt_version,
        timeout_seconds=int(_env("LLM_TIMEOUT_SECONDS", "180")),
        max_output_tokens=int(_env("LLM_MAX_OUTPUT_TOKENS", "220")),
        prompt_path=PROJECT_ROOT / "materials" / "prompts" / f"{prompt_version}.md",
        raw_data_dir=PROJECT_ROOT / "data" / "raw",
    )
