from __future__ import annotations
import logging
from typing import Any
from hindsight_client import Hindsight
from .config import get_settings

logger = logging.getLogger(__name__)

MISSION = """
You are the long-term memory for a software engineering code review team.
Prioritize durable coding standards, architectural decisions, security expectations,
recurring mistakes, accepted/rejected review feedback, and rationale behind design
choices. Ignore greetings and ephemeral conversational details. Preserve who made a
decision and why when that context matters. Prefer facts grounded in actual review
feedback over generic software advice.
"""


class HindsightService:
    def __init__(self) -> None:
        settings = get_settings()
        kwargs = {"base_url": settings.hindsight_api_url}
        if settings.hindsight_api_key:
            kwargs["api_key"] = settings.hindsight_api_key
        self.client = Hindsight(**kwargs)

    @staticmethod
    def bank_id(project: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in project.lower())
        return f"code-review-{safe[:70]}"

    def ensure_bank(self, project: str) -> str:
        bank_id = self.bank_id(project)
        try:
            self.client.create_bank(bank_id=bank_id, name=f"Code Review — {project}")
            self.client.update_bank_config(
                bank_id,
                retain_mission=MISSION,
                retain_extraction_mode="verbose",
                observations_mission=(
                    "Create durable observations about this team's coding standards, "
                    "architectural preferences, recurring review patterns, and feedback."
                ),
                reflect_mission=(
                    "You are a senior software architect. Ground answers in remembered "
                    "engineering decisions and review evidence. Prefer project-specific "
                    "conventions over generic advice."
                ),
                disposition_skepticism=4,
                disposition_literalism=4,
                disposition_empathy=1,
            )
        except Exception as exc:
            # Bank creation is idempotent in normal Hindsight usage. If it already exists,
            # configuration can still be updated. We keep the exception non-fatal so a
            # transient config call does not break a review.
            logger.debug("Hindsight bank setup: %s", exc)
            try:
                self.client.update_bank_config(
                    bank_id,
                    retain_mission=MISSION,
                    observations_mission=(
                        "Create durable observations about this team's coding standards, "
                        "architectural preferences, recurring review patterns, and feedback."
                    ),
                )
            except Exception as config_exc:
                logger.warning("Could not configure Hindsight bank %s: %s", bank_id, config_exc)
        return bank_id

    def recall(self, project: str, query: str) -> list[dict[str, Any]]:
        bank_id = self.ensure_bank(project)
        try:
            result = self.client.recall(
                bank_id=bank_id,
                query=query[:5000],
                types=["world", "experience", "observation"],
                max_tokens=3500,
            )
            memories = []
            for item in result.results:
                memories.append(
                    {
                        "id": str(getattr(item, "id", "")),
                        "text": getattr(item, "text", ""),
                        "type": getattr(item, "type", ""),
                        "context": getattr(item, "context", ""),
                    }
                )
            return memories
        except Exception as exc:
            logger.warning("Hindsight recall failed: %s", exc)
            return []

    def retain(
        self,
        project: str,
        content: str,
        context: str,
        tags: list[str] | None = None,
        document_id: str | None = None,
    ) -> bool:
        bank_id = self.ensure_bank(project)
        try:
            kwargs: dict[str, Any] = {
                "bank_id": bank_id,
                "content": content[:12000],
                "context": context,
                "timestamp": "unset",
            }
            if tags:
                kwargs["tags"] = tags
            if document_id:
                kwargs["document_id"] = document_id
            self.client.retain(**kwargs)
            return True
        except Exception as exc:
            logger.warning("Hindsight retain failed: %s", exc)
            return False

    def seed(self, project: str, memories: list[dict[str, Any]]) -> int:
        count = 0
        for idx, item in enumerate(memories):
            if self.retain(
                project=project,
                content=item["content"],
                context=item["context"],
                tags=item.get("tags"),
                document_id=f"seed-{project}-{idx}",
            ):
                count += 1
        return count


def get_hindsight_service() -> HindsightService:
    return HindsightService()
