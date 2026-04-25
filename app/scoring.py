from __future__ import annotations


def normalize_answer(answer: str | None) -> str:
    return (answer or "").strip().upper()


def score_answer(question: dict, answer: str | None) -> dict:
    normalized = normalize_answer(answer)
    correct_answer = normalize_answer(question["answer"])
    is_correct = normalized == correct_answer
    return {
        "question_id": question["id"],
        "answer": normalized,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "score": 1 if is_correct else 0,
    }


def score_assessment(questions: list[dict], answers: list[str | None]) -> dict:
    items = [score_answer(question, answer) for question, answer in zip(questions, answers)]
    return {
        "items": items,
        "score": sum(item["score"] for item in items),
        "total": len(questions),
    }
