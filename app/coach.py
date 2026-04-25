from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.config import Settings
from app.llm_client import LLMClientError, LLMResponsesClient


def load_guardrails(settings: Settings) -> str:
    if not settings.prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found for version '{settings.prompt_version}': {settings.prompt_path}"
        )
    return settings.prompt_path.read_text(encoding="utf-8").strip()


def build_module_context(module: dict, assessment_locked: bool) -> str:
    objectives = "\n".join(f"- {objective}" for objective in module.get("learning_objectives", []))
    state = "LOCKED" if assessment_locked else "UNLOCKED"
    return (
        f"Lesson metadata:\n"
        f"- Module ID: {module['module_id']}\n"
        f"- Title: {module['title']}\n"
        f"- Concepts: {', '.join(module.get('concepts', []))}\n"
        f"- Assessment state: {state}\n"
        f"- Learning objectives:\n{objectives}\n\n"
        f"Snippet under discussion:\n```cobol\n{module['snippet']}\n```"
    )


@dataclass
class CoachTurn:
    answer: str
    response_id: str | None
    latency_ms: int


class CobolCoach:
    def __init__(self, settings: Settings, module: dict):
        self.settings = settings
        self.module = module
        self.client = LLMResponsesClient(settings)
        self.base_guardrails = load_guardrails(settings)
        self.previous_response_id: str | None = None
        self.follow_up_count = 0

    def _developer_prompt(self, assessment_locked: bool) -> str:
        return (
            f"{self.base_guardrails}\n\n"
            f"{build_module_context(self.module, assessment_locked=assessment_locked)}"
        )

    def is_configured(self) -> bool:
        return self.client.is_configured()

    def uses_api(self) -> bool:
        return self.client.is_configured()

    def explain_module(self, on_text: Callable[[str], None] | None = None) -> CoachTurn:
        response = self.client.create_response(
            developer_prompt=self._developer_prompt(assessment_locked=False),
            user_prompt=(
                "Teach only the COBOL snippet in this module to a beginner programmer. "
                "Use these uppercase labels and no Markdown bold markers: BIG PICTURE:, "
                "BREAKDOWN:, and FINAL DISPLAY RESULT:. Do not include CHECKPOINT QUESTION: "
                "on this first lesson response. In BIG PICTURE, explain the general COBOL "
                "purpose or operation pattern, such as storing data, copying data, looping, "
                "using a table, checking a condition, or doing arithmetic; do not summarize "
                "by repeating variable or program names. In BREAKDOWN, briefly pick apart the COBOL like "
                "a tiny C function walkthrough: data names, PIC clauses, MOVE, DISPLAY, "
                "and any operator or condition in the snippet. Format BREAKDOWN as the "
                "header on its own line, then one '-' bullet per COBOL statement as "
                "'CODE: short explanation'. Remove the final period from CODE before the "
                "colon, and align the explanation colons vertically when possible. Do not use "
                "Markdown bold. Keep each explanation one short, simple, technical sentence. "
                "Do not introduce unrelated COBOL topics."
            ),
            on_text=on_text,
        )
        self.previous_response_id = response.response_id
        return CoachTurn(
            answer=response.output_text,
            response_id=response.response_id,
            latency_ms=response.latency_ms,
        )

    def answer_follow_up(
        self,
        learner_question: str,
        assessment_locked: bool = False,
        on_text: Callable[[str], None] | None = None,
    ) -> CoachTurn:
        if not learner_question.strip():
            raise LLMClientError("Please enter a question before asking the coach.")

        self.follow_up_count += 1
        checkpoint_instruction = (
            "You may add CHECKPOINT QUESTION: only if there is a useful learner checkpoint."
            if self.follow_up_count >= 3
            else "Do not include CHECKPOINT QUESTION: yet."
        )

        response = self.client.create_response(
            developer_prompt=self._developer_prompt(assessment_locked=assessment_locked),
            user_prompt=(
                f"{learner_question.strip()}\n\n"
                "Use YES: or NO: only when the learner asks an explicit yes/no question, "
                "such as one starting with is, are, does, do, can, should, or would. For "
                "open-ended questions like what, why, how, explain, or tell me, do not print "
                "YES: or NO:; answer directly. Never print both YES: and NO: in the same "
                "answer. Use BREAKDOWN: when the answer needs COBOL syntax picked apart. "
                f"{checkpoint_instruction}"
            ),
            previous_response_id=self.previous_response_id,
            on_text=on_text,
        )
        self.previous_response_id = response.response_id
        return CoachTurn(
            answer=response.output_text,
            response_id=response.response_id,
            latency_ms=response.latency_ms,
        )
