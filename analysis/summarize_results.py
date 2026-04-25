from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import csv
import statistics


RAW_RESULTS = Path(__file__).resolve().parents[1] / "data" / "raw" / "study_results.csv"


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(statistics.mean(values), 2)


def main() -> int:
    if not RAW_RESULTS.exists():
        print(f"No study results found at {RAW_RESULTS}")
        return 1

    with RAW_RESULTS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["condition"]].append(row)

    print(f"Loaded {len(rows)} sessions from {RAW_RESULTS}\n")
    for condition, items in sorted(grouped.items()):
        pre_scores = [float(item["pre_test_score"]) for item in items]
        post_scores = [float(item["post_test_score"]) for item in items]
        gains = [post - pre for pre, post in zip(pre_scores, post_scores)]
        durations = [float(item["timed_task_duration_seconds"]) for item in items]
        accuracy = [float(item["timed_task_accuracy"]) for item in items]

        print(f"{condition.upper()} condition")
        print(f"  Sessions: {len(items)}")
        print(f"  Mean pre-test: {mean(pre_scores)}")
        print(f"  Mean post-test: {mean(post_scores)}")
        print(f"  Mean gain: {mean(gains)}")
        print(f"  Mean timed accuracy: {mean(accuracy)}")
        print(f"  Mean timed duration (s): {mean(durations)}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
