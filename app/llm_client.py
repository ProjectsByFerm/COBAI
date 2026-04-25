from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from time import perf_counter
from urllib import error, request
import json
import ssl

from app.config import Settings


class LLMClientError(RuntimeError):
    """Raised when the LLM request fails."""


@dataclass
class LLMResponse:
    response_id: str | None
    output_text: str
    latency_ms: int
    raw_response: dict


def _extract_output_text(payload: dict) -> str:
    if payload.get("output_text"):
        return str(payload["output_text"]).strip()

    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                chunks.append(text)
    return "\n".join(chunk.strip() for chunk in chunks if chunk.strip())


def _is_certificate_error(exc: error.URLError) -> bool:
    reason = getattr(exc, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(reason)


def _certificate_error_message(reason: object) -> str:
    return (
        "LLM API request failed because Python could not verify the HTTPS certificate.\n"
        f"Details: {reason}\n\n"
        "On macOS Python installs from python.org, run the bundled certificate installer:\n"
        '  open "/Applications/Python 3.11/Install Certificates.command"\n\n'
        "If that file is not present, install or update the certifi package for this Python:\n"
        "  python3 -m pip install --upgrade certifi"
    )


class LLMResponsesClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def is_configured(self) -> bool:
        return bool(self.settings.api_key)

    def create_response(
        self,
        *,
        developer_prompt: str,
        user_prompt: str,
        previous_response_id: str | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        if not self.settings.api_key:
            raise LLMClientError("LLM_API_KEY is not set.")
        if not user_prompt.strip():
            raise LLMClientError("Cannot send an empty prompt to the LLM API.")

        prompt = f"{developer_prompt.strip()}\n\nLearner prompt:\n{user_prompt.strip()}"
        if self.settings.api_base_url.rstrip("/").endswith("/v1"):
            return self._create_ollama_response(prompt=prompt, on_text=on_text)

        payload: dict = {
            "model": self.settings.model,
            "max_output_tokens": self.settings.max_output_tokens,
            "input": [
                {"role": "user", "content": prompt},
            ],
        }
        if self.settings.reasoning_effort:
            payload["reasoning_effort"] = self.settings.reasoning_effort
        if self.settings.temperature is not None:
            payload["temperature"] = self.settings.temperature
        if previous_response_id and self.settings.previous_response_id_enabled:
            payload["previous_response_id"] = previous_response_id

        http_request = request.Request(
            self.settings.api_endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        start = perf_counter()
        try:
            with request.urlopen(http_request, timeout=self.settings.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMClientError(f"LLM API returned HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            if _is_certificate_error(exc):
                raise LLMClientError(_certificate_error_message(exc.reason)) from exc
            raise LLMClientError(f"LLM API request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMClientError(
                f"LLM API request timed out after {self.settings.timeout_seconds} seconds."
            ) from exc

        output_text = _extract_output_text(body)
        if not output_text:
            raise LLMClientError("LLM API returned no text output.")

        return LLMResponse(
            response_id=body.get("id"),
            output_text=output_text,
            latency_ms=int((perf_counter() - start) * 1000),
            raw_response=body,
        )

    def _create_ollama_response(
        self,
        *,
        prompt: str,
        on_text: Callable[[str], None] | None,
    ) -> LLMResponse:
        payload: dict = {
            "model": self.settings.model,
            "prompt": prompt,
            "stream": bool(on_text),
            "keep_alive": "10m",
            "options": {"num_predict": self.settings.max_output_tokens},
        }
        if self.settings.temperature is not None:
            payload["options"]["temperature"] = self.settings.temperature

        http_request = request.Request(
            self.settings.ollama_generate_endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        start = perf_counter()
        chunks: list[str] = []
        raw_chunks: list[dict] = []
        try:
            with request.urlopen(http_request, timeout=self.settings.timeout_seconds) as response:
                if on_text:
                    for line in response:
                        if not line.strip():
                            continue
                        chunk = json.loads(line.decode("utf-8"))
                        raw_chunks.append(chunk)
                        text = chunk.get("response", "")
                        if text:
                            chunks.append(text)
                            on_text(text)
                        if chunk.get("done"):
                            break
                else:
                    body = json.loads(response.read().decode("utf-8"))
                    raw_chunks.append(body)
                    text = body.get("response", "")
                    if text:
                        chunks.append(text)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMClientError(f"LLM API returned HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise LLMClientError(f"LLM API request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMClientError(
                f"LLM API request timed out after {self.settings.timeout_seconds} seconds."
            ) from exc

        output_text = "".join(chunks).strip()
        if not output_text:
            raise LLMClientError("LLM API returned no text output.")

        final_chunk = raw_chunks[-1] if raw_chunks else {}
        return LLMResponse(
            response_id=final_chunk.get("created_at"),
            output_text=output_text,
            latency_ms=int((perf_counter() - start) * 1000),
            raw_response={"chunks": raw_chunks} if on_text else final_chunk,
        )
