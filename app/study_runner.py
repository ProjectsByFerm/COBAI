from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter, sleep
import re
import sys
import textwrap

from app.coach import CobolCoach
from app.config import Settings, load_settings
from app.content_loader import list_modules, load_module, load_tutorial_text
from app.export_results import append_results
from app.llm_client import LLMClientError
from app.scoring import score_answer, score_assessment


LLM_SECTION_LABELS = (
    "big picture",
    "breakdown",
    "relevant lines",
    "final display result",
    "final visible result",
    "final result",
    "one unanswered checkpoint question",
    "one checkpoint question",
    "checkpoint question",
    "one hint",
    "hint",
)
LLM_SECTION_LABEL_DISPLAY_NAMES = {
    "relevant lines": "BREAKDOWN",
}
DISPLAY_SECTION_LABELS = (
    "BIG PICTURE",
    "BREAKDOWN",
    "FINAL DISPLAY RESULT",
    "FINAL VISIBLE RESULT",
    "FINAL RESULT",
    "CHECKPOINT QUESTION",
    "HINT",
)
LLM_SECTION_HEADER_PATTERN = re.compile(
    rf"^(\s*(?:[-*]\s+|\d+[.)]\s+)?)\*{{0,2}}\s*"
    rf"({'|'.join(re.escape(label) for label in LLM_SECTION_LABELS)})"
    rf"\s*:?\s*\*{{0,2}}\s*:?",
    re.IGNORECASE,
)
DISPLAY_SECTION_HEADER_PATTERN = re.compile(
    rf"^\s*(?:[-*]\s+|\d+[.)]\s+)?(?:{'|'.join(re.escape(label) for label in DISPLAY_SECTION_LABELS)}):",
)
BREAKDOWN_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*]\s+|\d+[.)]\s+)(?P<code>.+):\s*(?P<explanation>.*)$"
)
RESPONSE_SEPARATOR = "_" * 74
TYPEWRITER_DELAY_SECONDS = 0.001


@dataclass(frozen=True)
class RuntimeContext:
    settings: Settings
    module: dict
    coach: CobolCoach


def wrap(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            lines.append("")
        elif line.lstrip().startswith("-") or line.lstrip().startswith("```"):
            lines.append(line)
        else:
            lines.append(textwrap.fill(line, width=88, break_on_hyphens=False))
    return "\n".join(lines)


def print_snippet(snippet: str) -> None:
    snippet_lines = snippet.rstrip().splitlines() or [""]
    width = max(len(line) for line in snippet_lines)
    border = f"+-{'-' * width}-+"

    print("\nCOBOL snippet:\n")
    print(border)
    for line in snippet_lines:
        print(f"| {line.ljust(width)} |")
    print(border)
    print()


def print_llm_error(exc: LLMClientError) -> None:
    print("\nLLM request failed.\n")
    print(str(exc))


def format_llm_terminal_line(line: str) -> str:
    def replace_header(match: re.Match[str]) -> str:
        prefix, label = match.groups()
        separator = " " if match.end() < len(line) and not line[match.end()].isspace() else ""
        display_label = LLM_SECTION_LABEL_DISPLAY_NAMES.get(label.lower(), label.upper())
        return f"{prefix}{display_label}:{separator}"

    formatted = LLM_SECTION_HEADER_PATTERN.sub(replace_header, line, count=1)
    return formatted.replace("**", "")


def is_section_header(line: str) -> bool:
    return bool(DISPLAY_SECTION_HEADER_PATTERN.match(line.strip()))


def is_breakdown_header(line: str) -> bool:
    section_prefix = re.sub(r"^\s*(?:[-*]\s+|\d+[.)]\s+)?", "", line.strip())
    return section_prefix == "BREAKDOWN:"


def clean_breakdown_code(code: str) -> str:
    code = code.strip().strip("`").strip()
    code = code.replace("**", "")
    if code.endswith("."):
        code = code[:-1].rstrip()
    return code


def parse_breakdown_line(line: str) -> tuple[str, str] | None:
    match = BREAKDOWN_BULLET_PATTERN.match(line)
    if not match:
        return None

    code = clean_breakdown_code(match.group("code"))
    explanation = match.group("explanation").strip().replace("**", "")
    if not code or not explanation:
        return None

    return code, explanation


def format_breakdown_line(line: str, code_width: int) -> str:
    parsed = parse_breakdown_line(line)
    if not parsed:
        return line

    code, explanation = parsed
    return f"- {code.ljust(code_width)}: {explanation}"


def align_breakdown_lines(lines: list[str]) -> list[str]:
    formatted_lines = list(lines)
    index = 0
    while index < len(formatted_lines):
        if not is_breakdown_header(formatted_lines[index]):
            index += 1
            continue

        bullet_indices: list[int] = []
        index += 1
        while index < len(formatted_lines):
            line = formatted_lines[index]
            if is_section_header(line):
                break
            if parse_breakdown_line(line):
                bullet_indices.append(index)
            index += 1

        if bullet_indices:
            code_width = max(
                len(parse_breakdown_line(formatted_lines[line_index])[0])
                for line_index in bullet_indices
            )
            for line_index in bullet_indices:
                formatted_lines[line_index] = format_breakdown_line(
                    formatted_lines[line_index],
                    code_width=code_width,
                )

    return formatted_lines


def format_llm_terminal_text(text: str) -> str:
    lines = [format_llm_terminal_line(line) for line in text.splitlines()]
    return "\n".join(align_breakdown_lines(lines))


class TerminalLLMStream:
    def __init__(self) -> None:
        self.pending = ""
        self.breakdown_lines: list[str] = []

    def write(self, text: str) -> None:
        self.pending += text
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            self._write_line(line, newline=True)

    def flush(self) -> None:
        if self.pending:
            self._write_line(self.pending, newline=False)
            self.pending = ""
        self._flush_breakdown(newline=False)

    def _write_line(self, line: str, *, newline: bool) -> None:
        formatted_line = format_llm_terminal_line(line)

        if self.breakdown_lines:
            if is_section_header(formatted_line) and not is_breakdown_header(formatted_line):
                self._flush_breakdown(newline=True)
                self._typewrite(formatted_line + ("\n" if newline else ""))
            else:
                self.breakdown_lines.append(formatted_line)
            return

        if is_breakdown_header(formatted_line):
            self.breakdown_lines.append(formatted_line)
            return

        self._typewrite(formatted_line + ("\n" if newline else ""))

    def _flush_breakdown(self, *, newline: bool) -> None:
        if not self.breakdown_lines:
            return

        text = "\n".join(align_breakdown_lines(self.breakdown_lines))
        if newline:
            text += "\n"
        self._typewrite(text)
        self.breakdown_lines.clear()

    def _typewrite(self, text: str) -> None:
        for character in text:
            sys.stdout.write(character)
            sys.stdout.flush()
            if TYPEWRITER_DELAY_SECONDS > 0 and not character.isspace():
                sleep(TYPEWRITER_DELAY_SECONDS)


def print_response_separator() -> None:
    print(f"\n\n{RESPONSE_SEPARATOR}")


def ask_multiple_choice(question: dict) -> str:
    print(f"\n{question['prompt']}")
    for label, text in question["choices"].items():
        print(f"  {label}. {text}")
    return input("Your answer: ").strip()


def run_question_block(label: str, questions: list[dict]) -> dict:
    print(f"\n== {label} ==")
    answers = [ask_multiple_choice(question) for question in questions]
    return score_assessment(questions, answers)


def run_timed_task(question: dict) -> dict:
    print("\n== Timed Comprehension Task ==")
    print("Press Enter when you are ready to start the timer.")
    input()
    start = perf_counter()
    answer = ask_multiple_choice(question)
    result = score_answer(question, answer)
    result["duration_seconds"] = round(perf_counter() - start, 2)
    result["timeout"] = False
    return result


def collect_background() -> dict:
    print("\n== Background ==")
    return {
        "programming_experience_level": input("Programming experience (beginner/intermediate/advanced): ").strip(),
        "languages_known": input("Languages known (comma-separated): ").strip(),
        "prior_cobol_exposure": input("Prior COBOL exposure (none/little/some): ").strip(),
        "llm_familiarity": input("Familiarity with AI coding tools (none/low/medium/high): ").strip(),
    }


def collect_survey() -> dict:
    print("\n== Post-Session Survey ==")
    return {
        "confidence_rating": input("Confidence understanding this COBOL topic (1-5): ").strip(),
        "usefulness_rating": input("Usefulness of the learning support (1-5): ").strip(),
        "difficulty_rating": input("Perceived difficulty (1-5): ").strip(),
        "notes": input("Any notes about confusion or helpful parts: ").strip(),
    }


def load_runtime_context(module_id: str) -> RuntimeContext:
    settings = load_settings()
    module = load_module(module_id)
    return RuntimeContext(settings=settings, module=module, coach=CobolCoach(settings, module))


def llm_ready(context: RuntimeContext) -> bool:
    return context.coach.is_configured()


def coach_model_name(context: RuntimeContext) -> str:
    return context.settings.model


def llm_payload(turn: object | None) -> dict:
    if not turn:
        return {}
    return {
        "response_id": turn.response_id,
        "latency_ms": turn.latency_ms,
        "text": turn.answer,
    }


def build_record(
    *,
    participant_id: str,
    session_started_at: str,
    condition: str,
    context: RuntimeContext,
    background: dict,
    pre_test: dict,
    practice_result: dict,
    timed_result: dict,
    post_test: dict,
    survey: dict,
    llm_response: dict,
) -> dict:
    settings = context.settings
    module = context.module
    llm_condition = condition == "llm"

    return {
        "participant_id": participant_id,
        "session_started_at": session_started_at,
        "condition": condition,
        "module_id": module["module_id"],
        "content_version": module["content_version"],
        "prompt_version": settings.prompt_version if llm_condition else "",
        "guardrail_version": settings.prompt_version if llm_condition else "",
        "llm_model": coach_model_name(context) if llm_condition else "",
        "api_success": str(bool(llm_response)).lower(),
        "pre_test_score": pre_test["score"],
        "pre_test_total": pre_test["total"],
        "post_test_score": post_test["score"],
        "post_test_total": post_test["total"],
        "timed_task_accuracy": timed_result["score"],
        "timed_task_duration_seconds": timed_result["duration_seconds"],
        "practice_score": practice_result["score"],
        "programming_experience_level": background["programming_experience_level"],
        "languages_known": background["languages_known"],
        "prior_cobol_exposure": background["prior_cobol_exposure"],
        "llm_familiarity": background["llm_familiarity"],
        "confidence_rating": survey["confidence_rating"],
        "usefulness_rating": survey["usefulness_rating"],
        "difficulty_rating": survey["difficulty_rating"],
        "notes": survey["notes"],
        "llm_response": llm_response,
        "pre_test_detail": pre_test["items"],
        "post_test_detail": post_test["items"],
        "practice_detail": practice_result,
        "timed_task_detail": timed_result,
    }


def run_coach_mode(module_id: str) -> int:
    context = load_runtime_context(module_id)

    print(f"\n== {context.module['module_id']} | {context.module['title']} ==")
    print_snippet(context.module["snippet"])

    try:
        print("COBAI is thinking...\n")
        stream = TerminalLLMStream()
        first_turn = context.coach.explain_module(on_text=stream.write)
        stream.flush()
        print_response_separator()
    except LLMClientError as exc:
        print_llm_error(exc)
        return 1
    print()

    print("\nAsk follow-up questions about this lesson. Type 'quit' to end.")
    prompt = "\nQuestion: "
    while True:
        try:
            learner_question = input(prompt).strip()
        except EOFError:
            break
        if learner_question.lower() in {"quit", "exit"}:
            break
        if not learner_question:
            print("Please enter a question, or type 'quit' to end.")
            continue
        try:
            print("\nAnswer:\n")
            stream = TerminalLLMStream()
            turn = context.coach.answer_follow_up(learner_question, on_text=stream.write)
            stream.flush()
            print_response_separator()
        except LLMClientError as exc:
            print_llm_error(exc)
            return 1
        print()
        prompt = "\nNext question (or type quit): "

    return 0


def run_study_mode(module_id: str, condition: str, participant_id: str | None) -> int:
    context = load_runtime_context(module_id)

    participant_id = participant_id or f"P-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    session_started_at = datetime.now(timezone.utc).isoformat()

    print(f"\n== Study Session | {participant_id} | {condition.upper()} ==")
    print(f"Module: {context.module['module_id']} - {context.module['title']}")

    background = collect_background()
    pre_test = run_question_block("Pre-Test", context.module["pre_test"])

    llm_response: dict = {}
    if condition == "llm":
        print("\n== Guardrailed COBOL Coach ==")
        print_snippet(context.module["snippet"])
        try:
            print("COBAI is thinking...\n")
            stream = TerminalLLMStream()
            lesson_turn = context.coach.explain_module(on_text=stream.write)
            stream.flush()
            print_response_separator()
        except LLMClientError as exc:
            print_llm_error(exc)
            return 1
        llm_response = llm_payload(lesson_turn)
        print()
    else:
        print("\n== Static Tutorial ==")
        print(wrap(load_tutorial_text(context.module)))

    practice_result = score_answer(
        context.module["practice_question"],
        ask_multiple_choice(context.module["practice_question"]),
    )
    timed_result = run_timed_task(context.module["timed_task"])
    post_test = run_question_block("Post-Test", context.module["post_test"])
    survey = collect_survey()

    record = build_record(
        participant_id=participant_id,
        session_started_at=session_started_at,
        condition=condition,
        context=context,
        background=background,
        pre_test=pre_test,
        practice_result=practice_result,
        timed_result=timed_result,
        post_test=post_test,
        survey=survey,
        llm_response=llm_response,
    )

    jsonl_path, csv_path = append_results(context.settings.raw_data_dir, record)
    print("\nSession complete.")
    print(f"Results saved to:\n- {jsonl_path}\n- {csv_path}")
    return 0


def print_modules() -> int:
    print("\nAvailable modules:\n")
    for module in list_modules():
        concepts = ", ".join(module["concepts"])
        print(f"- {module['module_id']}: {module['title']} [{module['difficulty']}] :: {concepts}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="COBAI guardrailed COBOL learning agent and study runner"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-modules", help="List the available COBOL modules")

    coach_parser = subparsers.add_parser("coach", help="Run the COBOL coach")
    coach_parser.add_argument("--module", required=True, help="Module ID such as COBOL-MOVE-001")

    study_parser = subparsers.add_parser("study", help="Run one study session")
    study_parser.add_argument("--module", required=True, help="Module ID such as COBOL-MOVE-001")
    study_parser.add_argument("--condition", required=True, choices=["llm", "static"])
    study_parser.add_argument("--participant", default=None, help="Optional participant ID")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "list-modules":
        return print_modules()
    if args.command == "coach":
        return run_coach_mode(args.module)
    if args.command == "study":
        return run_study_mode(args.module, args.condition, args.participant)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
