from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["v1.7"])


class SuggestPlanRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    weak_topics: List[str] = Field(..., min_length=1)
    daily_hours: float = Field(default=2.0, gt=0, le=16)


class DayPlan(BaseModel):
    day: int
    focus_topic: str
    allocated_hours: float
    tasks: List[str]


class SuggestPlanResponse(BaseModel):
    student_id: str
    days: List[DayPlan]
    total_weekly_hours: float


class WeeklyParentReportRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    student_name: str = Field(..., min_length=1)
    week_start: str = Field(..., min_length=1)
    total_questions: int = Field(default=0, ge=0)
    correct_count: int = Field(default=0, ge=0)
    pomodoro_minutes: int = Field(default=0, ge=0)
    completed_tasks: int = Field(default=0, ge=0)
    total_tasks: int = Field(default=0, ge=0)


class WeeklyParentReportResponse(BaseModel):
    student_id: str
    student_name: str
    week_start: str
    accuracy_rate: float
    task_completion_rate: float
    pomodoro_hours: float
    summary: str


class LedgerEntry(BaseModel):
    delta_sessions: int
    reason: str = Field(..., min_length=1)
    recorded_at: Optional[str] = None


class SessionLedgerRequest(BaseModel):
    coach_id: str = Field(..., min_length=1)
    student_id: str = Field(..., min_length=1)
    entries: List[LedgerEntry] = Field(default_factory=list)


class SessionLedgerResponse(BaseModel):
    coach_id: str
    student_id: str
    total_added: int
    total_used: int
    remaining_balance: int
    status: str


@router.post("/ai/suggest-plan", response_model=SuggestPlanResponse)
def suggest_study_plan(payload: SuggestPlanRequest) -> SuggestPlanResponse:
    days: List[DayPlan] = []
    topic_count = len(payload.weak_topics)
    for idx in range(7):
        topic = payload.weak_topics[idx % topic_count]
        tasks = [
            f"{topic} konu anlatımı ve özet çıkarımı",
            f"{topic} ile ilgili 20 soruluk pekiştirme testi",
            "Yanlış yapılan soruların deftere işlenmesi",
        ]
        days.append(
            DayPlan(
                day=idx + 1,
                focus_topic=topic,
                allocated_hours=round(payload.daily_hours, 2),
                tasks=tasks,
            )
        )
    return SuggestPlanResponse(
        student_id=payload.student_id,
        days=days,
        total_weekly_hours=round(payload.daily_hours * 7, 2),
    )


@router.post("/reports/weekly-parent", response_model=WeeklyParentReportResponse)
def generate_weekly_parent_report(
    payload: WeeklyParentReportRequest,
) -> WeeklyParentReportResponse:
    accuracy = (
        round((payload.correct_count / payload.total_questions) * 100, 2)
        if payload.total_questions > 0
        else 0.0
    )
    completion = (
        round((payload.completed_tasks / payload.total_tasks) * 100, 2)
        if payload.total_tasks > 0
        else 0.0
    )
    pomodoro_hours = round(payload.pomodoro_minutes / 60.0, 2)
    summary = (
        f"{payload.student_name} için {payload.week_start} haftasında "
        f"{payload.total_questions} soru çözüldü (%{accuracy} doğruluk), "
        f"{pomodoro_hours} saat odaklanılmış çalışma yapıldı ve "
        f"görevlerin %{completion}'i tamamlandı."
    )
    return WeeklyParentReportResponse(
        student_id=payload.student_id,
        student_name=payload.student_name,
        week_start=payload.week_start,
        accuracy_rate=accuracy,
        task_completion_rate=completion,
        pomodoro_hours=pomodoro_hours,
        summary=summary,
    )


@router.post("/sessions/ledger", response_model=SessionLedgerResponse)
def calculate_session_ledger(payload: SessionLedgerRequest) -> SessionLedgerResponse:
    total_added = sum(e.delta_sessions for e in payload.entries if e.delta_sessions > 0)
    total_used = sum(-e.delta_sessions for e in payload.entries if e.delta_sessions < 0)
    remaining_balance = total_added - total_used
    status = "active" if remaining_balance > 0 else "depleted"
    return SessionLedgerResponse(
        coach_id=payload.coach_id,
        student_id=payload.student_id,
        total_added=total_added,
        total_used=total_used,
        remaining_balance=remaining_balance,
        status=status,
    )


@router.get("/sessions/ledger/{student_id}", response_model=SessionLedgerResponse)
def get_student_session_ledger(student_id: str) -> SessionLedgerResponse:
    return SessionLedgerResponse(
        coach_id="system",
        student_id=student_id,
        total_added=0,
        total_used=0,
        remaining_balance=0,
        status="depleted",
    )


@router.get("/system/capabilities")
def get_system_capabilities() -> dict:
    exam_groups = ["LGS", "TYT", "AYT", "YDT", "KPSS", "DGS", "ALES", "YDS"]
    active_modules = [
        "study_plan",
        "weekly_parent_report",
        "session_ledger",
        "pomodoro",
        "question_logs",
        "pwa_offline_sync",
    ]
    return {
        "status": "ok",
        "exam_groups": exam_groups,
        "exam_group_count": len(exam_groups),
        "active_modules": active_modules,
    }
