import os
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_code_review.db"

from app.github_service import parse_pr_url
from app.llm_service import LLMService
from app.review_engine import ReviewEngine


def test_parse_pr_url():
    assert parse_pr_url("https://github.com/acme/payments/pull/42") == ("acme", "payments", 42)


def test_parse_pr_url_rejects_non_github():
    try:
        parse_pr_url("https://gitlab.com/acme/payments/-/merge_requests/42")
        assert False
    except ValueError:
        assert True


def test_demo_review_uses_memory_signal():
    diff = """
    + repository interface PaymentRepository {}
    + if (amount <= 0) throw new InvalidPaymentException();
    """
    memories = [
        {"type": "world", "text": "Internal modules use concrete repositories."},
        {"type": "world", "text": "Monetary amounts must be validated."},
    ]
    result = LLMService().demo_review(diff, memories)
    assert result["memory_used"] == 2
    assert any(f["basis"] == "memory_backed" for f in result["findings"])


def test_memory_query_is_specific():
    query = ReviewEngine._memory_query(
        type("R", (), {"project": "payments-service", "language": "Java"})(),
        ["PaymentService.java"],
        "amount <= 0",
    )
    assert "payments-service" in query
    assert "PaymentService.java" in query
