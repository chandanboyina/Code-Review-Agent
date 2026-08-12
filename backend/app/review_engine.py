from __future__ import annotations
import hashlib
import json
from sqlalchemy.orm import Session

from .config import get_settings
from .github_service import fetch_pull_request
from .hindsight_service import HindsightService
from .llm_service import LLMService
from .models import Review, Feedback
from .schemas import ReviewRequest, ReviewResult, ReviewResponse


class ReviewEngine:
    def __init__(self, db: Session):
        self.db = db
        self.hindsight = HindsightService()
        self.llm = LLMService()
        self.settings = get_settings()

    def run(self, request: ReviewRequest) -> ReviewResponse:
        diff = request.diff
        source = "diff"
        pr_metadata = {}

        if request.pr_url:
            diff, pr_metadata = fetch_pull_request(request.pr_url)
            source = "github_pr"

        if not diff:
            raise ValueError("Provide either a GitHub PR URL or a diff/code change.")

        if len(diff) > self.settings.max_diff_chars:
            diff = diff[: self.settings.max_diff_chars] + "\n\n[TRUNCATED]"

        files_changed = self._extract_files(diff)
        query = self._memory_query(request, files_changed, diff)

        memories = self.hindsight.recall(request.project, query)
        result = self.llm.review(request.project, request.language, diff, memories)

        # Retain a compact, durable summary instead of blindly retaining the entire diff.
        review_fingerprint = hashlib.sha256(diff.encode("utf-8")).hexdigest()[:16]
        self.hindsight.retain(
            project=request.project,
            content=self._review_memory_content(request, result, files_changed, pr_metadata),
            context="code review outcome",
            tags=[f"project:{request.project}", "topic:review"],
            document_id=f"review-{review_fingerprint}",
        )

        row = Review(
            project=request.project,
            reviewer=request.reviewer,
            language=request.language,
            source=source,
            pr_url=request.pr_url or "",
            diff_text=diff,
            result_json=json.dumps(result),
            memory_json=json.dumps(memories),
            memory_used=len(memories),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        return ReviewResponse(
            review_id=row.id,
            project=request.project,
            source=source,
            result=ReviewResult.model_validate(result),
            memories=memories,
            diff_preview=diff[:5000],
        )

    def feedback(self, review_id: int, finding_id: str, decision: str, comment: str) -> Feedback:
        review = self.db.get(Review, review_id)
        if not review:
            raise ValueError("Review not found.")

        feedback = Feedback(
            review_id=review_id,
            finding_id=finding_id,
            decision=decision,
            comment=comment,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        try:
            result = json.loads(review.result_json)
            finding = next(
                (f for f in result.get("findings", []) if f.get("id") == finding_id),
                None,
            )
            finding_text = finding.get("title", "finding") if finding else finding_id
        except Exception:
            finding_text = finding_id

        self.hindsight.retain(
            project=review.project,
            content=(
                f"Review feedback from {review.reviewer}: finding {finding_id} "
                f"('{finding_text}') was {decision}. "
                f"Reviewer comment: {comment or 'No comment provided.'} "
                f"This feedback should influence future code reviews."
            ),
            context="reviewer feedback",
            tags=[f"project:{review.project}", "topic:review-feedback", f"decision:{decision}"],
            document_id=f"feedback-{feedback.id}",
        )
        return feedback

    @staticmethod
    def _memory_query(request: ReviewRequest, files_changed: list[str], diff: str) -> str:
        code_excerpt = diff[:3000]
        return (
            f"Project: {request.project}. Language: {request.language}. "
            f"Changed files: {', '.join(files_changed[:20])}. "
            f"What team coding standards, architecture decisions, previous review "
            f"feedback, rejected suggestions, and recurring mistakes are relevant to "
            f"this change? Code excerpt: {code_excerpt}"
        )

    @staticmethod
    def _review_memory_content(
        request: ReviewRequest,
        result: dict,
        files_changed: list[str],
        pr_metadata: dict,
    ) -> str:
        findings = result.get("findings", [])
        finding_lines = []
        for f in findings[:10]:
            finding_lines.append(
                f"- {f.get('title')}: severity={f.get('severity')}, "
                f"basis={f.get('basis')}, suggestion={f.get('suggestion')}"
            )
        return (
            f"Code review outcome for project {request.project}, language {request.language}. "
            f"Changed files: {', '.join(files_changed[:20])}. "
            f"PR title: {pr_metadata.get('title', '')}. "
            f"Review verdict: {result.get('verdict')}, score={result.get('score')}. "
            f"Findings:\n" + "\n".join(finding_lines)
        )

    @staticmethod
    def _extract_files(diff: str) -> list[str]:
        files = []
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                files.append(line[6:].strip())
        return list(dict.fromkeys(files))
