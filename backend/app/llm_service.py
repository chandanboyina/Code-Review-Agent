from __future__ import annotations
import json
import logging
from openai import OpenAI
from .config import get_settings
from .prompts import REVIEW_SYSTEM_PROMPT, REVIEW_USER_TEMPLATE

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.enabled = bool(settings.llm_api_key) and not settings.demo_mode
        self.client = (
            OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
            if self.enabled
            else None
        )

    def review(self, project: str, language: str, diff: str, memories: list[dict]) -> dict:
        if not self.enabled:
            return self.demo_review(diff, memories)

        memory_text = "\n".join(
            f"- [{m.get('type', 'memory')}] {m.get('text', '')}" for m in memories
        ) or "No relevant team memory was found."

        prompt = REVIEW_USER_TEMPLATE.format(
            project=project,
            language=language,
            memories=memory_text,
            diff=diff,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            return self._normalize(result, len(memories))
        except Exception as exc:
            logger.exception("LLM review failed; falling back to deterministic review: %s", exc)
            return self.demo_review(diff, memories)

    @staticmethod
    def _normalize(result: dict, memory_count: int) -> dict:
        result.setdefault("summary", "Review completed.")
        result["score"] = max(0, min(100, int(result.get("score", 75))))
        result.setdefault("verdict", "approve_with_changes")
        result.setdefault("findings", [])
        result.setdefault("learned_signals", [])
        result["memory_used"] = memory_count
        result.setdefault("next_review_focus", [])

        for idx, finding in enumerate(result["findings"], start=1):
            finding.setdefault("id", f"F-{idx:03d}")
            finding.setdefault("severity", "medium")
            finding.setdefault("category", "maintainability")
            finding.setdefault("title", "Review finding")
            finding.setdefault("explanation", "Review this change carefully.")
            finding.setdefault("suggestion", "Consider improving the implementation.")
            finding.setdefault("basis", "current_code")
            finding.setdefault("memory_refs", [])
        return result

    @staticmethod
    def demo_review(diff: str, memories: list[dict]) -> dict:
        text = diff.lower()
        findings = []

        if "repository interface" in text or ("interface" in text and "repository" in text):
            memory_hit = any(
                "concrete repository" in m.get("text", "").lower()
                or "repository interface" in m.get("text", "").lower()
                for m in memories
            )
            if memory_hit:
                findings.append(
                    {
                        "id": "F-001",
                        "severity": "info",
                        "category": "architecture",
                        "title": "Repository interface matches remembered team decision",
                        "explanation": (
                            "This pattern was explicitly discussed before. Team memory "
                            "says internal payment modules use concrete repositories."
                        ),
                        "suggestion": "Keep the concrete repository unless the boundary has changed.",
                        "line": None,
                        "basis": "memory_backed",
                        "memory_refs": [
                            "Internal payment modules intentionally use concrete repositories."
                        ],
                    }
                )

        if "amount" in text and ("< 0" in text or "<= 0" in text or "negative" in text):
            findings.append(
                {
                    "id": "F-002",
                    "severity": "medium",
                    "category": "correctness",
                    "title": "Payment amount validation is present",
                    "explanation": "The change validates a monetary amount before processing.",
                    "suggestion": "Keep the domain validation at the service boundary.",
                    "line": None,
                    "basis": "memory_backed" if memories else "current_code",
                    "memory_refs": ["Monetary amounts must be validated before payment processing."]
                    if memories
                    else [],
                }
            )

        if "runtimeexception" in text or "throw new exception" in text:
            findings.append(
                {
                    "id": "F-003",
                    "severity": "medium",
                    "category": "architecture",
                    "title": "Generic exception may bypass the domain error model",
                    "explanation": (
                        "The change appears to use a generic exception instead of a "
                        "project-specific domain exception."
                    ),
                    "suggestion": "Use the project's domain exception hierarchy.",
                    "line": None,
                    "basis": "memory_backed" if memories else "best_practice",
                    "memory_refs": ["Business failures use the project's domain exception hierarchy."]
                    if memories
                    else [],
                }
            )

        if not findings:
            findings.append(
                {
                    "id": "F-001",
                    "severity": "info",
                    "category": "maintainability",
                    "title": "No high-confidence issue detected",
                    "explanation": (
                        "The deterministic fallback did not find a high-confidence issue "
                        "in the supplied change."
                    ),
                    "suggestion": "Run the review with a configured LLM for deeper semantic analysis.",
                    "line": None,
                    "basis": "current_code",
                    "memory_refs": [],
                }
            )

        score = 94 if all(f["severity"] in {"info", "low"} for f in findings) else 82
        verdict = "approve" if score >= 90 else "approve_with_changes"

        return {
            "summary": (
                "Demo review completed. Team memory was consulted before evaluating "
                "the change."
            ),
            "score": score,
            "verdict": verdict,
            "findings": findings,
            "learned_signals": [
                m.get("text", "")[:180] for m in memories[:3] if m.get("text")
            ],
            "memory_used": len(memories),
            "next_review_focus": [
                "Check whether future feedback confirms or rejects this architectural pattern."
            ],
        }
