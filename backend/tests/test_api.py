import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: E402
from optical_parser import parse_optical_csv, parse_optical_csv_to_json  # noqa: E402

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_exam_success():
    payload = {
        "exam_name": "TYT Deneme 1",
        "topics": [
            {"topic_name": "Türev", "correct": 8, "wrong": 4, "empty": 0},
            {"topic_name": "İntegral", "correct": 3, "wrong": 4, "empty": 3},
        ],
    }
    response = client.post("/api/analyze-exam", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["exam_name"] == "TYT Deneme 1"
    assert data["total_net"] == 9.0
    assert data["recommended_focus_topic"] == "İntegral"
    assert data["weakest_topic_details"]["mastery_percentage"] == 20.0
    assert len(data["topics"]) == 2
    assert data["topics"][0]["net"] == 7.0
    assert data["topics"][0]["mastery_percentage"] == 58.33


def test_analyze_exam_empty_topics():
    response = client.post("/api/analyze-exam", json={"exam_name": "TYT", "topics": []})
    assert response.status_code == 400


def test_analyze_exam_zero_questions():
    payload = {
        "exam_name": "TYT",
        "topics": [{"topic_name": "Limit", "correct": 0, "wrong": 0, "empty": 0}],
    }
    response = client.post("/api/analyze-exam", json=payload)
    assert response.status_code == 400


def test_optical_parser_batch_valid_and_invalid():
    csv_data = (
        "student_name,subject,topic,correct,wrong,empty\n"
        "Ali Yılmaz,Matematik,Türev,6,4,0\n"
        "Ayşe Demir,Fizik,Optik,4,0,6\n"
        "Mehmet Kaya,Kimya,Mol,-1,2,3\n"
        "Zeynep Ak,Biyoloji,Hücre,abc,1,2\n"
        "Can Öz,Türkçe,,5,0,0\n"
        "Ece Tan,Tarih,Osmanlı,0,0,0\n"
    )
    result = parse_optical_csv(csv_data)

    assert result["total_rows"] == 6
    assert result["valid_count"] == 2
    assert result["error_count"] == 4
    assert len(result["records"]) == 2
    assert len(result["errors"]) == 4

    first = result["records"][0]
    assert first["student_name"] == "Ali Yılmaz"
    assert first["net"] == 5.0
    assert first["mastery_pct"] == 50.0

    second = result["records"][1]
    assert second["net"] == 4.0
    assert second["mastery_pct"] == 40.0

    assert result["summary"]["average_net"] == 4.5
    assert result["summary"]["average_mastery_pct"] == 45.0

    error_lines = [err["line"] for err in result["errors"]]
    assert error_lines == [4, 5, 6, 7]


def test_optical_parser_missing_columns():
    csv_data = "student_name,subject,topic,correct,wrong\nAli,Matematik,Türev,5,0\n"
    result = parse_optical_csv(csv_data)
    assert result["valid_count"] == 0
    assert result["error_count"] == 1
    assert "Missing required columns" in result["errors"][0]["error"]


def test_optical_parser_to_json():
    csv_data = "student_name,subject,topic,correct,wrong,empty\nAli,Matematik,Türev,8,4,8\n"
    raw_json = parse_optical_csv_to_json(csv_data)
    parsed = json.loads(raw_json)
    assert parsed["valid_count"] == 1
    assert parsed["records"][0]["net"] == 7.0
    assert parsed["records"][0]["mastery_pct"] == 35.0
