from fastapi.testclient import TestClient

try:
    from main import app
except ImportError:
    from backend.main import app

client = TestClient(app)


def test_suggest_plan_success():
    payload = {
        "student_id": "stu-1",
        "weak_topics": ["Türev", "İntegral"],
        "daily_hours": 2.5,
    }
    response = client.post("/api/v1/ai/suggest-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "stu-1"
    assert len(data["days"]) == 7
    assert data["total_weekly_hours"] == 17.5
    assert data["days"][0]["focus_topic"] == "Türev"
    assert data["days"][1]["focus_topic"] == "İntegral"


def test_suggest_plan_empty_topics_returns_422():
    payload = {
        "student_id": "stu-1",
        "weak_topics": [],
        "daily_hours": 2.0,
    }
    response = client.post("/api/v1/ai/suggest-plan", json=payload)
    assert response.status_code == 422


def test_weekly_parent_report_success():
    payload = {
        "student_id": "stu-2",
        "student_name": "Ayşe Yılmaz",
        "week_start": "2026-11-23",
        "total_questions": 200,
        "correct_count": 160,
        "pomodoro_minutes": 300,
        "completed_tasks": 8,
        "total_tasks": 10,
    }
    response = client.post("/api/v1/reports/weekly-parent", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["accuracy_rate"] == 80.0
    assert data["task_completion_rate"] == 80.0
    assert data["pomodoro_hours"] == 5.0
    assert "Ayşe Yılmaz" in data["summary"]


def test_weekly_parent_report_zero_totals():
    payload = {
        "student_id": "stu-3",
        "student_name": "Mehmet Demir",
        "week_start": "2026-11-23",
        "total_questions": 0,
        "correct_count": 0,
        "pomodoro_minutes": 0,
        "completed_tasks": 0,
        "total_tasks": 0,
    }
    response = client.post("/api/v1/reports/weekly-parent", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["accuracy_rate"] == 0.0
    assert data["task_completion_rate"] == 0.0


def test_sessions_ledger_active_and_depleted():
    active_payload = {
        "coach_id": "coach-1",
        "student_id": "stu-1",
        "entries": [
            {"delta_sessions": 8, "reason": "Paket satın alımı"},
            {"delta_sessions": -3, "reason": "Tamamlanan seanslar"},
        ],
    }
    res_active = client.post("/api/v1/sessions/ledger", json=active_payload)
    assert res_active.status_code == 200
    data_active = res_active.json()
    assert data_active["total_added"] == 8
    assert data_active["total_used"] == 3
    assert data_active["remaining_balance"] == 5
    assert data_active["status"] == "active"

    depleted_payload = {
        "coach_id": "coach-1",
        "student_id": "stu-1",
        "entries": [
            {"delta_sessions": 4, "reason": "Paket"},
            {"delta_sessions": -4, "reason": "Tamamlandı"},
        ],
    }
    res_depleted = client.post("/api/v1/sessions/ledger", json=depleted_payload)
    assert res_depleted.status_code == 200
    assert res_depleted.json()["remaining_balance"] == 0
    assert res_depleted.json()["status"] == "depleted"

def test_get_student_session_ledger():
    response = client.get("/api/v1/sessions/ledger/stu-42")
    assert response.status_code == 200
    data = response.json()
    assert data["coach_id"] == "system"
    assert data["student_id"] == "stu-42"
    assert data["total_added"] == 0
    assert data["total_used"] == 0
    assert data["remaining_balance"] == 0
    assert data["status"] == "depleted"

def test_get_system_capabilities():
    response = client.get("/api/v1/system/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["exam_group_count"] == 8
    assert "TYT" in data["exam_groups"]
    assert "study_plan" in data["active_modules"]
    assert "pwa_offline_sync" in data["active_modules"]
    
