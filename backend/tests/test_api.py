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

def test_import_optical_csv_success():
    csv_data = "student_name,subject,topic,correct,wrong,empty\nAli Yilmaz,Matematik,Turev,6,4,0\nAyse Demir,Fizik,Optik,4,0,6\n"
    response = client.post("/api/import-optical-csv", json={"csv_text": csv_data})
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["valid_count"] == 2
    assert data["error_count"] == 0
    assert data["summary"]["average_net"] == 4.5


def test_parent_report_success():
    payload = {
        "student_name": "Ali Yilmaz",
        "exam_type": "YKS",
        "completed_tasks": 8,
        "total_tasks": 10,
        "last_net": 52.5,
        "focus_minutes": 180,
        "study_streak": 5,
        "mood": "normal",
        "weak_topics": ["Turev", "Optik"],
    }
    response = client.post("/api/parent-report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ("normal", "medium", "high")
    assert isinstance(data["weekly_actions"], list)
    assert len(data["weekly_actions"]) == 3
    assert isinstance(data["report_text"], str)
    assert len(data["report_text"]) > 0
    
def test_response_caching():
    exam_payload = {
        "exam_name": "Cache Test Deneme",
        "topics": [
            {"topic_name": "Matematik", "correct": 30, "wrong": 4, "empty": 6},
        ],
    }
    first_exam = client.post("/api/analyze-exam", json=exam_payload)
    assert first_exam.status_code == 200
    assert first_exam.json()["cached"] is False

    second_exam = client.post("/api/analyze-exam", json=exam_payload)
    assert second_exam.status_code == 200
    assert second_exam.json()["cached"] is True

    parent_payload = {
        "student_name": "Zeynep Kaya",
        "exam_type": "YKS",
        "completed_tasks": 7,
        "total_tasks": 10,
        "last_net": 60.0,
        "focus_minutes": 200,
        "study_streak": 4,
        "mood": "normal",
        "weak_topics": ["Optik"],
    }
    first_parent = client.post("/api/parent-report", json=parent_payload)
    assert first_parent.status_code == 200
    assert first_parent.json()["cached"] is False

    second_parent = client.post("/api/parent-report", json=parent_payload)
    assert second_parent.status_code == 200
    assert second_parent.json()["cached"] is True
 

def test_billing_quote_monthly_and_yearly():
    monthly_res = client.post(
        "/api/billing/quote",
        json={"plan": "starter", "billing_cycle": "monthly"},
    )
    assert monthly_res.status_code == 200
    monthly_data = monthly_res.json()
    assert monthly_data["plan"] == "starter"
    assert monthly_data["billing_cycle"] == "monthly"
    assert monthly_data["discount_rate"] == 0.0
    assert monthly_data["student_quota"] == 40
    assert monthly_data["total_amount"] == monthly_data["kdv_dahil_tutar"]
    assert monthly_data["total_amount"] == round(990.0 * 1.20, 2)
    assert len(monthly_data["features"]) > 0

    yearly_res = client.post(
        "/api/billing/quote",
        json={"plan": "pro", "billing_cycle": "yearly"},
    )
    assert yearly_res.status_code == 200
    yearly_data = yearly_res.json()
    assert yearly_data["plan"] == "pro"
    assert yearly_data["billing_cycle"] == "yearly"
    assert yearly_data["discount_rate"] == 0.20
    assert yearly_data["student_quota"] == 50
    expected_subtotal = round(999.0 * 12 * 0.80, 2)
    assert yearly_data["subtotal_excl_vat"] == expected_subtotal
    assert yearly_data["total_amount"] == round(expected_subtotal * 1.20, 2)


def test_notify_parent_email_dry_run(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    res = client.post(
        "/api/notify/parent-email",
        json={
            "parent_email": "veli@example.com",
            "student_name": "Ali Yilmaz",
            "report_text": "Bu hafta 250 soru cozuldu ve deneme neti 72.5 oldu.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "dry_run"
    assert data["to"] == "veli@example.com"
    assert "Ali Yilmaz" in data["subject"]
    assert "250 soru" in data["preview"]   

def test_rbac_blocks_student_on_coach_endpoints():
    res_csv = client.post(
        "/api/import-optical-csv",
        headers={"X-User-Role": "student"},
        json={"csv_text": "student_name,subject,topic,correct,wrong,empty\nAli Yilmaz,Matematik,Turev,6,4,0\n"},
    )
    assert res_csv.status_code == 403

    res_email = client.post(
        "/api/notify/parent-email",
        headers={"X-User-Role": "student"},
        json={
            "parent_email": "veli@example.com",
            "student_name": "Ali Yilmaz",
            "report_text": "Haftalik rapor",
        },
    )
    assert res_email.status_code == 403


EMAIL_BODY = {"parent_email": "veli@example.com", "student_name": "Ali", "report_text": "Rapor"}


def _use_supabase(monkeypatch, memberships):
    """Configure real auth and replace the two Supabase calls with fakes."""
    import main

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    main._rate_limit_store.clear()

    def fake_get(path, token):
        if token != "good":
            raise main.HTTPException(status_code=401, detail="invalid")
        return {"id": "user-1"} if path == "/auth/v1/user" else memberships

    monkeypatch.setattr(main, "_supabase_get", fake_get)


def test_auth_ignores_role_header_when_supabase_configured(monkeypatch):
    _use_supabase(monkeypatch, [{"role": "coach"}])
    res = client.post("/api/notify/parent-email", headers={"X-User-Role": "coach"}, json=EMAIL_BODY)
    assert res.status_code == 401


def test_auth_rejects_bad_token(monkeypatch):
    _use_supabase(monkeypatch, [{"role": "coach"}])
    res = client.post("/api/notify/parent-email", headers={"Authorization": "Bearer bad"}, json=EMAIL_BODY)
    assert res.status_code == 401


def test_auth_rejects_user_without_staff_membership(monkeypatch):
    _use_supabase(monkeypatch, [])
    res = client.post("/api/notify/parent-email", headers={"Authorization": "Bearer good"}, json=EMAIL_BODY)
    assert res.status_code == 403


def test_auth_allows_coach(monkeypatch):
    _use_supabase(monkeypatch, [{"role": "coach"}])
    res = client.post("/api/notify/parent-email", headers={"Authorization": "Bearer good"}, json=EMAIL_BODY)
    assert res.status_code == 200
    assert res.json()["status"] == "dry_run"


def test_real_email_is_refused_without_auth_configuration(monkeypatch):
    import main

    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    main._rate_limit_store.clear()

    def must_not_send(*args, **kwargs):
        raise AssertionError("no outgoing request expected")

    monkeypatch.setattr(main.urllib.request, "urlopen", must_not_send)
    res = client.post("/api/notify/parent-email", json=EMAIL_BODY)
    assert res.status_code == 503


def test_subscription_state_machine():
    expired_trial = client.post(
        "/api/subscription/evaluate",
        json={
            "status": "trial",
            "plan": "trial",
            "trial_days_left": 0,
            "current_students": 2,
        },
    )
    assert expired_trial.status_code == 200
    expired_data = expired_trial.json()
    assert expired_data["effective_status"] == "read_only"
    assert expired_data["can_write"] is False

    full_mini = client.post(
        "/api/subscription/evaluate",
        json={
            "status": "active",
            "plan": "mini",
            "trial_days_left": 0,
            "current_students": 5,
        },
    )
    assert full_mini.status_code == 200
    mini_data = full_mini.json()
    assert mini_data["student_limit"] == 5
    assert mini_data["remaining_seats"] == 0
    assert mini_data["can_add_student"] is False


def test_request_id_header_present():
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-Id" in res.headers
    assert len(res.headers["X-Request-Id"]) > 0
    

def test_redis_cache_put_and_get(monkeypatch):
    import main

    store = {}

    class FakeRedis:
        def setex(self, key, ttl, value):
            store[key] = (ttl, value)

        def get(self, key):
            entry = store.get(key)
            return entry[1] if entry is not None else None

    monkeypatch.setattr(main, "_redis_client", FakeRedis())
    main._response_cache.clear()

    payload = {"topic": "Türev", "score": 90}
    main._cache_put("unit-test-key", payload)

    assert "adimplan:cache:unit-test-key" in store
    assert store["adimplan:cache:unit-test-key"][0] == 3600
    assert "unit-test-key" not in main._response_cache
    assert main._cache_get("unit-test-key") == payload


def test_redis_cache_fallback_to_memory_on_error(monkeypatch):
    import main

    class BrokenRedis:
        def setex(self, key, ttl, value):
            raise ConnectionError("redis unavailable")

        def get(self, key):
            raise ConnectionError("redis unavailable")

    monkeypatch.setattr(main, "_redis_client", BrokenRedis())
    main._response_cache.clear()

    payload = {"plan": "Matematik", "hours": 4}
    main._cache_put("fallback-key", payload)

    assert main._response_cache.get("fallback-key") == payload
    assert main._cache_get("fallback-key") == payload


def test_redis_rate_limit_exceeded_and_fallback_to_memory(monkeypatch):
    import main

    counts = {}

    class FakeRedis:
        def incr(self, key):
            counts[key] = counts.get(key, 0) + 1
            return counts[key]

        def expire(self, key, ttl):
            return True

    class BrokenRedis:
        def incr(self, key):
            raise ConnectionError("redis unavailable")

        def expire(self, key, ttl):
            raise ConnectionError("redis unavailable")

    req_payload = {
        "status": "active",
        "plan": "mini",
        "trial_days_left": 0,
        "current_students": 1,
    }
    monkeypatch.setattr(main, "RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr(main, "_redis_client", FakeRedis())
    main._rate_limit_store.clear()

    assert client.post("/api/subscription/evaluate", json=req_payload).status_code == 200
    assert client.post("/api/subscription/evaluate", json=req_payload).status_code == 200
    limited = client.post("/api/subscription/evaluate", json=req_payload)
    assert limited.status_code == 429
    assert limited.json() == {"detail": "Rate limit exceeded."}

    monkeypatch.setattr(main, "_redis_client", BrokenRedis())
    main._rate_limit_store.clear()

    assert client.post("/api/subscription/evaluate", json=req_payload).status_code == 200
    assert client.post("/api/subscription/evaluate", json=req_payload).status_code == 200
    fallback_limited = client.post("/api/subscription/evaluate", json=req_payload)
    assert fallback_limited.status_code == 429
    main._rate_limit_store.clear()

