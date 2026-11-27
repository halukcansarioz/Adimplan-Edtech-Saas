import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import OrderedDict
from typing import Dict, List, Literal, Optional, Set

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from optical_parser import parse_optical_csv
except ImportError:
    from backend.optical_parser import parse_optical_csv

app = FastAPI(title="Adimplan EdTech Analytics API", version="1.4.0")
try:
    from v17_routes import router as v17_router
except ImportError:
    from backend.v17_routes import router as v17_router

app.include_router(v17_router)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
    except ImportError:
        pass
REDIS_URL = os.getenv("REDIS_URL")
_redis_client = None
if REDIS_URL:
    try:
        import redis
        _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
        _redis_client.ping()
    except Exception:
        _redis_client = None
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60
# The e-mail endpoint can send real mail, so it gets a much tighter limit.
NOTIFY_PATH = "/api/notify/parent-email"
NOTIFY_RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_MAX_KEYS = 10_000
CACHE_MAX_ENTRIES = 500
_rate_limit_store: Dict[str, List[float]] = {}
_response_cache: "OrderedDict[str, dict]" = OrderedDict()


def _redis_limit_exceeded(limits) -> bool:
    for key, limit in limits:
        rkey = f"adimplan:rl:{key}"
        count = _redis_client.incr(rkey)
        if count == 1:
            _redis_client.expire(rkey, RATE_LIMIT_WINDOW_SECONDS)
        if count > limit:
            return True
    return False


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Health probes and CORS preflights must not consume the quota.
    if request.method == "OPTIONS" or request.url.path == "/health":
        return await call_next(request)
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    limits = [(client_ip, RATE_LIMIT_REQUESTS)]
    if request.url.path == NOTIFY_PATH:
        limits.append((f"{client_ip}|notify", NOTIFY_RATE_LIMIT_REQUESTS))
    if _redis_client is not None:
        try:
            exceeded = _redis_limit_exceeded(limits)
        except Exception:
            pass  # Redis unavailable: fall back to the in-memory limiter below
        else:
            if exceeded:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded."})
            return await call_next(request)

    if len(_rate_limit_store) >= RATE_LIMIT_MAX_KEYS:
        for key in [k for k, v in _rate_limit_store.items() if not v or v[-1] <= window_start]:
            del _rate_limit_store[key]

    for key, limit in limits:
        timestamps = [ts for ts in _rate_limit_store.get(key, []) if ts > window_start]
        _rate_limit_store[key] = timestamps
        if len(timestamps) >= limit:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded."})
    for key, _ in limits:
        _rate_limit_store[key].append(now)
    return await call_next(request)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-Id") or str(uuid.uuid4())
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected internal server error occurred.",
            "request_id": request_id,
        },
        headers={"X-Request-Id": request_id},
    )


ALLOWED_ROLES = {"super_admin", "institution_admin", "coach", "student", "parent"}
COACH_OR_ADMIN_ROLES = {"super_admin", "institution_admin", "coach"}


def require_role(request: Request, allowed_roles: Optional[Set[str]] = None) -> str:
    role = (request.headers.get("X-User-Role") or "coach").strip().lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail=f"Invalid or unauthorized role: {role}")
    target_roles = allowed_roles if allowed_roles is not None else ALLOWED_ROLES
    if role not in target_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not permitted to access this resource.",
        )
    return role


# Added after the other middlewares so it wraps them: 429 responses keep their CORS headers.
DEFAULT_ALLOWED_ORIGINS = (
    "https://adimplan.vercel.app,https://adimplan-edtech-saas.vercel.app,"
    "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500"
)
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Id", "X-User-Role"],
    expose_headers=["X-Request-Id"],
)


# Real authentication: active when both variables are set. The caller's Supabase
# access token is verified with Supabase, and the role comes from public.memberships
# (only an owner can change it once migration 004 is applied). Without them the API
# runs in demo mode, where X-User-Role is client-controlled and proves nothing.
def _supabase_settings():
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    return (url, key) if url and key else None


def _supabase_get(path: str, token: str):
    url, key = _supabase_settings()
    req = urllib.request.Request(
        f"{url}{path}",
        headers={"apikey": key, "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise HTTPException(status_code=401, detail="Oturum gecersiz veya suresi dolmus. Tekrar giris yapin.")
        raise HTTPException(status_code=503, detail="Kimlik dogrulama servisine ulasilamadi.")
    except Exception:
        raise HTTPException(status_code=503, detail="Kimlik dogrulama servisine ulasilamadi.")


def require_staff(request: Request) -> Optional[str]:
    """Allow only coaches and owners. Returns the user id, or None in demo mode."""
    if _supabase_settings() is None:
        require_role(request, COACH_OR_ADMIN_ROLES)
        return None
    scheme, _, token = (request.headers.get("Authorization") or "").partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bu islem icin giris yapmalisiniz.")
    user = _supabase_get("/auth/v1/user", token)
    user_id = user.get("id") if isinstance(user, dict) else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Oturum gecersiz veya suresi dolmus. Tekrar giris yapin.")
    query = urllib.parse.urlencode(
        {"select": "role", "user_id": f"eq.{user_id}", "role": "in.(owner,coach)", "limit": "1"}
    )
    if not _supabase_get(f"/rest/v1/memberships?{query}", token):
        raise HTTPException(status_code=403, detail="Bu islem yalnizca koc ve kurum sahipleri icindir.")
    return user_id


def _make_cache_key(prefix: str, payload: BaseModel) -> str:
    raw = json.dumps(payload.model_dump(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(f"{prefix}:{raw}".encode("utf-8")).hexdigest()


def _cache_get(key: str):
    if _redis_client is not None:
        try:
            raw = _redis_client.get(f"adimplan:cache:{key}")
            if raw is not None:
                return json.loads(raw)
        except Exception:
            pass
    value = _response_cache.get(key)
    if value is not None:
        _response_cache.move_to_end(key)
    return value


def _cache_put(key: str, value: dict) -> None:
    if _redis_client is not None:
        try:
            _redis_client.setex(f"adimplan:cache:{key}", 3600, json.dumps(value, ensure_ascii=False))
            return
        except Exception:
            pass
    _response_cache[key] = value
    _response_cache.move_to_end(key)
    while len(_response_cache) > CACHE_MAX_ENTRIES:
        _response_cache.popitem(last=False)


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
    cached = _cache_get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}
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
    _cache_put(cache_key, result)
    return {**result, "cached": False}

class OpticalCsvImportRequest(BaseModel):
    csv_text: str

@app.post("/api/import-optical-csv")
def import_optical_csv(request: Request, payload: OpticalCsvImportRequest):
    require_staff(request)
    if not payload.csv_text or not payload.csv_text.strip():
        raise HTTPException(status_code=400, detail="csv_text is required.")
    return parse_optical_csv(payload.csv_text)

class ParentReportRequest(BaseModel):
    student_name: str = Field(..., min_length=1)
    exam_type: str = Field(default="YKS")
    completed_tasks: int = Field(..., ge=0)
    total_tasks: int = Field(..., ge=0)
    last_net: float  # may be negative: wrong answers are penalised
    focus_minutes: int = Field(..., ge=0)
    study_streak: int = Field(..., ge=0)
    mood: str = Field(default="normal")
    weak_topics: List[str] = Field(default_factory=list)


@app.post("/api/parent-report")
def generate_parent_report(payload: ParentReportRequest):
    cache_key = _make_cache_key("parent_report", payload)
    cached = _cache_get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}
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

    weak_list = [t.strip() for t in payload.weak_topics if t.strip()]
    if len(weak_list) >= 3:
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
    _cache_put(cache_key, result)
    return {**result, "cached": False}


class BillingQuoteRequest(BaseModel):
    plan: Literal["trial", "baslangic", "pro", "kurumsal", "mini", "starter", "medium"]
    billing_cycle: Literal["monthly", "yearly"] = "monthly"


BILLING_PLANS = {"trial": {"monthly_price": 0.0, "student_quota": 5, "features": ["5 ogrenci kotasi", "14 gun ucretsiz deneme"]}, "baslangic": {"monthly_price": 499.0, "student_quota": 15, "features": ["15 ogrenci kotasi", "Temel YKS/LGS takip", "Haftalik rapor"]}, "pro": {"monthly_price": 999.0, "student_quota": 50, "features": ["50 ogrenci kotasi", "AI deneme analizi", "Veli PDF/E-posta raporu"]}, "kurumsal": {"monthly_price": 0.0, "student_quota": 99999, "features": ["99999 ogrenci kotasi", "Ozel kurum alan adi & PWA", "iyzico/PayTR tahsilat & API erisimi"]}}
PLAN_CATALOG = {**BILLING_PLANS,
    "mini": {
        "monthly_price": 490.0,
        "student_quota": 15,
        "features": ["15 ogrenci kotasi", "Temel YKS/LGS takip", "Haftalik rapor"],
    },
    "starter": {
        "monthly_price": 990.0,
        "student_quota": 40,
        "features": ["40 ogrenci kotasi", "AI deneme analizi", "Veli PDF/E-posta raporu"],
    },
    "medium": {
        "monthly_price": 1990.0,
        "student_quota": 120,
        "features": ["120 ogrenci kotasi", "Coklu koc yonetimi", "Oncelikli AI & bildirimler"],
    },
}


@app.post("/api/billing/quote")
def billing_quote(payload: BillingQuoteRequest):
    plan_info = PLAN_CATALOG[payload.plan]
    monthly_price = plan_info["monthly_price"]
    if payload.billing_cycle == "yearly":
        discount_rate = 0.20
        subtotal = round(monthly_price * 12 * (1 - discount_rate), 2)
    else:
        discount_rate = 0.0
        subtotal = round(monthly_price, 2)

    vat_rate = 0.20
    vat_amount = round(subtotal * vat_rate, 2)
    total_with_vat = round(subtotal + vat_amount, 2)

    return {
        "plan": payload.plan,
        "billing_cycle": payload.billing_cycle,
        "currency": "TRY",
        "subtotal_excl_vat": subtotal,
        "discount_rate": discount_rate,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total_amount": total_with_vat,
        "kdv_dahil_tutar": total_with_vat,
        "student_quota": plan_info["student_quota"],
        "features": plan_info["features"],
        "payment_providers_ready": ["iyzico", "paytr"],
    }


class ParentEmailRequest(BaseModel):
    # Exactly one plain address: no lists, display names or line breaks.
    parent_email: str = Field(..., min_length=5, max_length=254, pattern=r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")
    student_name: str = Field(..., min_length=1, max_length=120)
    report_text: str = Field(..., min_length=1, max_length=10_000)


@app.post("/api/notify/parent-email")
def notify_parent_email(request: Request, payload: ParentEmailRequest):
    require_staff(request)
    subject = f"Adimplan Haftalik Veli Raporu - {' '.join(payload.student_name.split())}"
    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()

    if not resend_api_key:
        return {
            "status": "dry_run",
            "provider": "resend",
            "to": payload.parent_email,
            "subject": subject,
            "student_name": payload.student_name,
            "preview": payload.report_text[:300],
        }

    # Never send real mail on the strength of a client-supplied role header.
    if _supabase_settings() is None:
        raise HTTPException(
            status_code=503,
            detail="E-posta gonderimi kapali: sunucuda SUPABASE_URL ve SUPABASE_ANON_KEY tanimlanmali.",
        )

    from_email = os.getenv("RESEND_FROM_EMAIL", "Adimplan <noreply@adimplan.com>")
    body = json.dumps({
        "from": from_email,
        "to": [payload.parent_email],
        "subject": subject,
        "text": payload.report_text,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        return {
            "status": "sent",
            "provider": "resend",
            "to": payload.parent_email,
            "subject": subject,
            "resend_response": resp_data,
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=502, detail=f"Resend API hatasi: {detail}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"E-posta gonderim hatasi: {str(exc)}")

SUBSCRIPTION_PLAN_LIMITS = {
    "trial": 5,
    "mini": 5,
    "starter": 25,
    "medium": 100,
    "baslangic": BILLING_PLANS["baslangic"]["student_quota"], "pro": BILLING_PLANS["pro"]["student_quota"], "kurumsal": BILLING_PLANS["kurumsal"]["student_quota"],
    "enterprise": 10000,
}


class SubscriptionEvaluateRequest(BaseModel):
    status: Literal["trial", "active", "past_due", "read_only", "canceled"]
    plan: Literal["trial", "baslangic", "pro", "kurumsal", "mini", "starter", "medium", "enterprise"]
    trial_days_left: int = Field(default=14, ge=0)
    current_students: int = Field(default=0, ge=0)


@app.post("/api/subscription/evaluate")
def evaluate_subscription(payload: SubscriptionEvaluateRequest):
    student_limit = SUBSCRIPTION_PLAN_LIMITS[payload.plan]
    remaining_seats = max(0, student_limit - payload.current_students)
    effective_status = (
        "read_only"
        if payload.status == "trial" and payload.trial_days_left <= 0
        else payload.status
    )
    can_write = effective_status in {"trial", "active"}
    can_add_student = can_write and payload.current_students < student_limit
    return {
        "status": payload.status,
        "effective_status": effective_status,
        "plan": payload.plan,
        "trial_days_left": payload.trial_days_left,
        "current_students": payload.current_students,
        "student_limit": student_limit,
        "remaining_seats": remaining_seats,
        "can_write": can_write,
        "can_add_student": can_add_student,
    }
    
