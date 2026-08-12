from __future__ import annotations
import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .hindsight_service import HindsightService
from .models import Review, Feedback
from .prompts import SEED_MEMORIES
from .review_engine import ReviewEngine
from .schemas import FeedbackRequest, HealthResponse, ReviewRequest, ReviewResponse


settings = get_settings()
app = FastAPI(
    title="Code Review Agent",
    version="1.0.0",
    description="A memory-aware code review agent powered by Hindsight.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/health", response_model=HealthResponse)
def health():
    hindsight_status = "configured"
    llm_status = "configured" if settings.llm_api_key and not settings.demo_mode else "demo-fallback"
    try:
        HindsightService().ensure_bank("health-check")
    except Exception:
        hindsight_status = "unreachable"
    return HealthResponse(
        status="ok",
        hindsight=hindsight_status,
        llm=llm_status,
    )


@app.post("/api/reviews", response_model=ReviewResponse)
def create_review(payload: ReviewRequest, db: Session = Depends(get_db)):
    try:
        return ReviewEngine(db).run(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Review failed: {exc}")


@app.get("/api/reviews")
def list_reviews(
    project: str = Query(default="default-project"),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Review)
        .filter(Review.project == project)
        .order_by(Review.created_at.desc())
        .limit(25)
        .all()
    )
    return [
        {
            "id": r.id,
            "project": r.project,
            "reviewer": r.reviewer,
            "language": r.language,
            "source": r.source,
            "memory_used": r.memory_used,
            "created_at": r.created_at.isoformat(),
            "result": json.loads(r.result_json),
        }
        for r in rows
    ]


@app.get("/api/reviews/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_db)):
    row = db.get(Review, review_id)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found.")
    return {
        "id": row.id,
        "project": row.project,
        "reviewer": row.reviewer,
        "language": row.language,
        "source": row.source,
        "pr_url": row.pr_url,
        "memory_used": row.memory_used,
        "result": json.loads(row.result_json),
        "memories": json.loads(row.memory_json),
        "diff_preview": row.diff_text[:5000],
        "created_at": row.created_at.isoformat(),
    }


@app.post("/api/reviews/{review_id}/feedback")
def add_feedback(
    review_id: int,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
):
    try:
        feedback = ReviewEngine(db).feedback(
            review_id,
            payload.finding_id,
            payload.decision,
            payload.comment,
        )
        return {
            "ok": True,
            "feedback_id": feedback.id,
            "message": "Feedback retained as team memory.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/demo/seed")
def seed_demo(
    project: str = Query(default="payments-service"),
):
    count = HindsightService().seed(project, SEED_MEMORIES)
    return {
        "ok": True,
        "project": project,
        "seeded": count,
        "message": (
            "Team memory seeded. Run a review, provide feedback, then run a similar "
            "review to demonstrate learning."
        ),
    }


@app.get("/api/memory")
def recall_memory(
    project: str = Query(default="payments-service"),
    q: str = Query(default="What coding standards and architecture decisions has the team learned?"),
):
    memories = HindsightService().recall(project, q)
    return {"project": project, "query": q, "count": len(memories), "memories": memories}


@app.get("/api/stats")
def stats(
    project: str = Query(default="payments-service"),
    db: Session = Depends(get_db),
):
    review_count = db.query(Review).filter(Review.project == project).count()
    feedback_count = (
        db.query(Feedback)
        .join(Review, Feedback.review_id == Review.id)
        .filter(Review.project == project)
        .count()
    )
    memory_hits = (
        db.query(Review)
        .filter(Review.project == project)
        .with_entities(Review.memory_used)
        .all()
    )
    total_memory_hits = sum(x[0] or 0 for x in memory_hits)
    return {
        "project": project,
        "reviews": review_count,
        "feedback_events": feedback_count,
        "memory_hits": total_memory_hits,
        "learning_loop": feedback_count > 0 and review_count > 0,
    }
