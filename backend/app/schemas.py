from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ReviewRequest(BaseModel):
    project: str = Field(default="default-project", min_length=2, max_length=120)
    reviewer: str = Field(default="demo-user", min_length=2, max_length=120)
    language: str = Field(default="unknown", max_length=40)
    pr_url: Optional[str] = Field(default="")
    diff: Optional[str] = Field(default="")

    @field_validator("project")
    @classmethod
    def clean_project(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "-")

    @field_validator("pr_url", "diff")
    @classmethod
    def normalize_optional(cls, value: Optional[str]) -> str:
        return (value or "").strip()


class FeedbackRequest(BaseModel):
    finding_id: str = Field(min_length=2, max_length=40)
    decision: Literal["accepted", "rejected", "corrected"]
    comment: str = Field(default="", max_length=2000)


class Finding(BaseModel):
    id: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str
    title: str
    explanation: str
    suggestion: str
    line: Optional[int] = None
    basis: Literal["memory_backed", "current_code", "best_practice"] = "current_code"
    memory_refs: list[str] = []


class ReviewResult(BaseModel):
    summary: str
    score: int = Field(ge=0, le=100)
    verdict: Literal["approve", "approve_with_changes", "request_changes"]
    findings: list[Finding]
    learned_signals: list[str] = []
    memory_used: int = 0
    next_review_focus: list[str] = []


class ReviewResponse(BaseModel):
    review_id: int
    project: str
    source: str
    result: ReviewResult
    memories: list[dict]
    diff_preview: str


class HealthResponse(BaseModel):
    status: str
    hindsight: str
    llm: str
