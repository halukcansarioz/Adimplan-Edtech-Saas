from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
try:
    from optical_parser import parse_optical_csv
except ImportError:
    from backend.optical_parser import parse_optical_csv
    
app = FastAPI(title="AdimPlan EdTech Analytics API", version="0.1.0")


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
    return {
        "exam_name": payload.exam_name,
        "total_net": round(total_net, 2),
        "topics": analyzed_topics,
        "recommended_focus_topic": weakest_topic["topic_name"],
        "weakest_topic_details": weakest_topic,
    }

class OpticalCsvImportRequest(BaseModel):
    csv_text: str

@app.post("/api/import-optical-csv")
def import_optical_csv(payload: OpticalCsvImportRequest):
    if not payload.csv_text or not payload.csv_text.strip():
      raise HTTPException(status_code=400, detail="csv_text is required.")
return parse_optical_csv(payload.csv_text)
