import csv
import io
import json
from typing import Any, Dict, List


REQUIRED_COLUMNS = ("student_name", "subject", "topic", "correct", "wrong", "empty")


def _parse_non_negative_int(value: Any, field_name: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"Missing value for '{field_name}'")
    try:
        parsed = int(str(value).strip())
    except ValueError as exc:
        raise ValueError(f"Invalid integer for '{field_name}': {value}") from exc
    if parsed < 0:
        raise ValueError(f"Negative value for '{field_name}': {parsed}")
    return parsed

def _detect_delimiter(csv_content: str) -> str:
    first_line = next((line for line in csv_content.splitlines() if line.strip()), "")
    counts = {d: first_line.count(d) for d in (",", ";", "|")}
    best = max((",", ";", "|"), key=lambda d: counts[d])
    return best if counts[best] > 0 else ","
    
def parse_optical_csv(csv_content: str) -> Dict[str, Any]:
    if not csv_content or not csv_content.strip():
        return {
            "total_rows": 0,
            "valid_count": 0,
            "error_count": 0,
            "records": [],
            "errors": [],
            "summary": {
                "average_net": 0.0,
                "average_mastery_pct": 0.0,
            },
        }

    reader = csv.DictReader(io.StringIO(csv_content.strip()), delimiter=_detect_delimiter(csv_content))
    fieldnames = [col.strip() for col in (reader.fieldnames or []) if col]
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
    if missing_columns:
        return {
            "total_rows": 0,
            "valid_count": 0,
            "error_count": 1,
            "records": [],
            "errors": [
                {
                    "line": 1,
                    "row": {},
                    "error": f"Missing required columns: {', '.join(missing_columns)}",
                }
            ],
            "summary": {
                "average_net": 0.0,
                "average_mastery_pct": 0.0,
            },
        }

    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for line_num, raw_row in enumerate(reader, start=2):
        row = {
            (k.strip() if k else k): (v.strip() if isinstance(v, str) else v)
            for k, v in raw_row.items()
        }
        try:
            if None in raw_row:
                raise ValueError("Row has extra columns beyond header")

            student_name = row.get("student_name") or ""
            subject = row.get("subject") or ""
            topic = row.get("topic") or ""

            if not student_name or not subject or not topic:
                raise ValueError("student_name, subject, and topic must be non-empty")

            correct = _parse_non_negative_int(row.get("correct"), "correct")
            wrong = _parse_non_negative_int(row.get("wrong"), "wrong")
            empty = _parse_non_negative_int(row.get("empty"), "empty")

            total_questions = correct + wrong + empty
            if total_questions <= 0:
                raise ValueError("Total question count must be greater than zero")

            net = round(correct - (wrong * 0.25), 2)
            mastery_pct = round((max(0.0, net) / total_questions) * 100.0, 2)

            records.append(
                {
                    "line": line_num,
                    "student_name": student_name,
                    "subject": subject,
                    "topic": topic,
                    "correct": correct,
                    "wrong": wrong,
                    "empty": empty,
                    "total_questions": total_questions,
                    "net": net,
                    "mastery_pct": mastery_pct,
                }
            )
        except ValueError as exc:
            errors.append(
                {
                    "line": line_num,
                    "row": row,
                    "error": str(exc),
                }
            )

    valid_count = len(records)
    error_count = len(errors)
    average_net = round(sum(r["net"] for r in records) / valid_count, 2) if valid_count else 0.0
    average_mastery_pct = (
        round(sum(r["mastery_pct"] for r in records) / valid_count, 2) if valid_count else 0.0
    )

    return {
        "total_rows": valid_count + error_count,
        "valid_count": valid_count,
        "error_count": error_count,
        "records": records,
        "errors": errors,
        "summary": {
            "average_net": average_net,
            "average_mastery_pct": average_mastery_pct,
        },
    }


def parse_optical_csv_to_json(csv_content: str) -> str:
    return json.dumps(parse_optical_csv(csv_content), ensure_ascii=False, indent=2)
