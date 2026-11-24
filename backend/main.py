from typing import List, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import hashlib
import json
import os
import time
from collections import defaultdict
try:
    from optical_parser import parse_optical_csv
except ImportError:
    from backend.optical_parser import parse_optical_csv
    
app = FastAPI(title="İvme Akademi EdTech Analytics API", version="0.1.0")
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
    except ImportError:
        pass

RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)
_response_cache: Dict[str, dict] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    timestamps = [ts for ts in _rate_limit_store[client_ip] if ts > window_start]
    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        _rate_limit_store[client_ip] = timestamps
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded."},
        )
    timestamps.append(now)
    _rate_limit_store[client_ip] = timestamps
    return await call_next(request)


def _make_cache_key(prefix: str, payload: BaseModel) -> str:
    raw = json.dumps(payload.model_dump(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(f"{prefix}:{raw}".encode("utf-8")).hexdigest()
    

class TopicResult(BaseModel):
    topic_name: str = Field(..., min_length=1)
    correct: int = Field(..., ge=0)
    wrong: int = Field(..., ge=0)
    empty: int = Field(..., ge=0)


class ExamAnalysisRequest(BaseModel):
    exam_name: str = Field(default="TYT Deneme")
    topics: List[TopicResult]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/analyze-exam")
def analyze_exam(payload: ExamAnalysisRequest):
    if not payload.topics:
        raise HTTPException(status_code=400, detail="At least one topic is required.")
    cache_key = _make_cache_key("analyze_exam", payload)
    if cache_key in _response_cache:
        return {**_response_cache[cache_key], "cached": True}
    analyzed_topics = []
    total_net = 0.0
    for item in payload.topics:
        total_questions = item.correct + item.wrong + item.empty
        if total_questions == 0:
            raise HTTPException(status_code=400, detail=f"Topic '{item.topic_name}' has 0 questions.")
        net = round(item.correct - (item.wrong / 4.0), 2)
        mastery_pct = round(max(0.0, net) / total_questions * 100.0, 2)
        total_net += net
        analyzed_topics.append({
            "topic_name": item.topic_name,
            "total_questions": total_questions,
            "net": net,
            "mastery_percentage": mastery_pct,
        })
    weakest_topic = min(analyzed_topics, key=lambda x: x["mastery_percentage"])
    result = {
        "exam_name": payload.exam_name,
        "total_net": round(total_net, 2),
        "topics": analyzed_topics,
        "recommended_focus_topic": weakest_topic["topic_name"],
        "weakest_topic_details": weakest_topic,
    }
    _response_cache[cache_key] = result
    return {**result, "cached": False}

class OpticalCsvImportRequest(BaseModel):
    csv_text: str

@app.post("/api/import-optical-csv")
def import_optical_csv(payload: OpticalCsvImportRequest):
    if not payload.csv_text or not payload.csv_text.strip():
      raise HTTPException(status_code=400, detail="csv_text is required.")
    return parse_optical_csv(payload.csv_text)

class ParentReportRequest(BaseModel):
    student_name: str = Field(..., min_length=1)
    exam_type: str = Field(default="YKS")
    completed_tasks: int = Field(..., ge=0)
    total_tasks: int = Field(..., ge=0)
    last_net: float = Field(..., ge=0)
    focus_minutes: int = Field(..., ge=0)
    study_streak: int = Field(..., ge=0)
    mood: str = Field(default="normal")
    weak_topics: List[str] = Field(default_factory=list)


@app.post("/api/parent-report")
def generate_parent_report(payload: ParentReportRequest):
    cache_key = _make_cache_key("parent_report", payload)
    if cache_key in _response_cache:
        return {**_response_cache[cache_key], "cached": True}
    completion_rate = (
        round((payload.completed_tasks / payload.total_tasks) * 100, 1)
        if payload.total_tasks > 0
        else 0.0
    )

    risk_score = 0
    if payload.total_tasks > 0 and completion_rate < 50:
        risk_score += 2
    elif payload.total_tasks > 0 and completion_rate < 75:
        risk_score += 1

    if payload.focus_minutes < 180:
        risk_score += 2
    elif payload.focus_minutes < 360:
        risk_score += 1

    if payload.study_streak == 0:
        risk_score += 2
    elif payload.study_streak < 3:
        risk_score += 1

    mood_norm = payload.mood.strip().lower()
    if mood_norm in {"low", "anxious", "stressed", "tired", "kaygili", "yorgun", "kotu", "1", "2"}:
        risk_score += 1

    if len(payload.weak_topics) >= 3:
        risk_score += 1

    if risk_score >= 4:
        risk_level = "high"
        risk_label = "Yuksek Risk"
    elif risk_score >= 2:
        risk_level = "medium"
        risk_label = "Orta Risk"
    else:
        risk_level = "normal"
        risk_label = "Normal"

    weak_list = [t.strip() for t in payload.weak_topics if t.strip()]
    weak_text = ", ".join(weak_list) if weak_list else "Belirtilen kritik zayif konu yok"

    action_1 = (
        f"Oncelikli zayif konu ({weak_list[0]}) icin haftada en az 3 gun 40'ar soruluk hedef test cozumu ve yanlis analizi yapilmali."
        if weak_list
        else f"{payload.exam_type} deneme analizine gore yanlis yapilan soru tiplerinden gunluk 20 soruluk tekrar blogu eklenmeli."
    )
    action_2 = (
        f"Haftalik odak suresini ({payload.focus_minutes} dk) artirmak icin gunde en az 2x45 dk Pomodoro blogu ile gorev tamamlama orani %80 uzerine cikarilmali."
        if completion_rate < 80 or payload.focus_minutes < 360
        else f"Mevcut {payload.study_streak} gunluk calisma serisi ve {payload.focus_minutes} dk odak temposu korunarak haftalik 1 adet sureli deneme uygulanmali."
    )
    action_3 = (
        f"Duygu durumu ('{payload.mood}') goz onunde bulundurularak haftalik kocluk gorusmesinde sinav kaygisi/motivasyon degerlendirmesi yapilmali ve uyku-dinlenme dengesi desteklenmeli."
        if risk_level in {"medium", "high"}
        else f"Veli-ogrenci haftalik degerlendirme toplantisinda {payload.last_net} net performansi pekistirilmeli ve bir sonraki hafta hedefi netlestirilmeli."
    )
    weekly_actions = [action_1, action_2, action_3]

    report_text = (
        f"İVME AKADEMİ HAFTALIK VELI BILGILENDIRME RAPORU\n"
        f"Ogrenci: {payload.student_name} | Sinav Turu: {payload.exam_type}\n"
        f"Gorev Tamamlama: {payload.completed_tasks}/{payload.total_tasks} (%{completion_rate})\n"
        f"Son Deneme Neti: {payload.last_net} | Odak Suresi: {payload.focus_minutes} dk | Calisma Serisi: {payload.study_streak} gun\n"
        f"Duygu Durumu (Mood): {payload.mood}\n"
        f"Zayif Konular: {weak_text}\n"
        f"Risk Seviyesi Onerisi: {risk_label} ({risk_level})\n\n"
        f"Haftalik 3 Somut Aksiyon Onerisi:\n"
        f"1. {weekly_actions[0]}\n"
        f"2. {weekly_actions[1]}\n"
        f"3. {weekly_actions[2]}"
    )

    result = {
        "student_name": payload.student_name,
        "exam_type": payload.exam_type,
        "completion_rate": completion_rate,
        "risk_level": risk_level,
        "weekly_actions": weekly_actions,
        "report_text": report_text,
    }
    _response_cache[cache_key] = result
    return {**result, "cached": False}
