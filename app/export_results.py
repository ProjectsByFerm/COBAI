from __future__ import annotations

from pathlib import Path
import csv
import json


CSV_FILE = "study_results.csv"
JSONL_FILE = "study_results.jsonl"


def _flatten_record(record: dict) -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value, ensure_ascii=True, sort_keys=True)
        elif value is None:
            flat[key] = ""
        else:
            flat[key] = str(value)
    return flat


def append_results(raw_dir: Path, record: dict) -> tuple[Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = raw_dir / JSONL_FILE
    csv_path = raw_dir / CSV_FILE

    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    flat_record = _flatten_record(record)
    existing_rows: list[dict[str, str]] = []
    existing_fields: list[str] = []

    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            existing_fields = reader.fieldnames or []
            existing_rows = list(reader)

    fieldnames = existing_fields + [field for field in flat_record if field not in existing_fields]
    if not fieldnames:
        fieldnames = list(flat_record.keys())

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        writer.writerow({field: flat_record.get(field, "") for field in fieldnames})

    return jsonl_path, csv_path
