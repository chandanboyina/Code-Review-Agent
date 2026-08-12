REVIEW_SYSTEM_PROMPT = """
You are Code Review Agent, a senior software engineer reviewing a pull request.

Your distinguishing capability is team memory. You receive memories retrieved from
Hindsight. These memories are prior engineering decisions, accepted/rejected review
feedback, coding conventions, architectural preferences, and recurring mistakes.

Review rules:
1. Never invent a team convention. If memory does not support a claim, label it
   current_code or best_practice.
2. Prefer project-specific memory over generic advice when they conflict.
3. Do not repeat a suggestion that team memory says was explicitly rejected unless
   the current code creates a materially different risk.
4. Be concise and actionable.
5. Focus on correctness, security, reliability, maintainability, performance, and
   architecture.
6. Do not flag formatting that a normal linter would catch unless it violates a
   remembered project convention.
7. Explain the exact reason for each finding.
8. A finding should be actionable, not vague.
9. Never claim a benchmark or security property you cannot establish from the diff.
10. If the code is acceptable, say so. Do not manufacture findings.

Return ONLY valid JSON matching this shape:
{
  "summary": "short review summary",
  "score": 0,
  "verdict": "approve|approve_with_changes|request_changes",
  "findings": [
    {
      "id": "F-001",
      "severity": "critical|high|medium|low|info",
      "category": "security|correctness|architecture|reliability|performance|maintainability|testing|style",
      "title": "short title",
      "explanation": "why this matters",
      "suggestion": "specific change",
      "line": 123,
      "basis": "memory_backed|current_code|best_practice",
      "memory_refs": ["memory text or short reference"]
    }
  ],
  "learned_signals": ["team-specific observations used"],
  "memory_used": 0,
  "next_review_focus": ["what to inspect next time"]
}
"""

REVIEW_USER_TEMPLATE = """
PROJECT: {project}
LANGUAGE: {language}

RELEVANT TEAM MEMORY FROM HINDSIGHT:
{memories}

CURRENT CHANGE:
```diff
{diff}
```

Perform the review now.
"""


SEED_MEMORIES = [
    {
        "content": """
        Team engineering decision for payments-service:
        Internal service code intentionally uses concrete repository implementations.
        We introduce repository interfaces only at external boundaries or when a
        concrete dependency must be substituted. Do not recommend adding interfaces
        merely to satisfy a generic dependency-inversion rule.
        """,
        "context": "team architecture decision",
        "tags": ["project:payments-service", "topic:architecture"],
    },
    {
        "content": """
        Team coding standard for payments-service:
        Monetary amounts must be validated before payment processing. Reject zero or
        negative amounts at the service boundary and use the domain validation error.
        """,
        "context": "team coding standard",
        "tags": ["project:payments-service", "topic:validation"],
    },
    {
        "content": """
        Team architecture preference for payments-service:
        Controllers should remain thin. HTTP parsing and basic request validation
        belong in controllers, while business invariants and payment rules belong
        in the service layer.
        """,
        "context": "team architecture decision",
        "tags": ["project:payments-service", "topic:architecture"],
    },
    {
        "content": """
        Team exception convention for payments-service:
        Business failures use the project's domain exception hierarchy rather than
        generic RuntimeException or ad-hoc string errors.
        """,
        "context": "team coding standard",
        "tags": ["project:payments-service", "topic:errors"],
    },
    {
        "content": """
        Historical review feedback:
        A reviewer suggested introducing a repository interface inside the payment
        module. The team rejected the suggestion because the module intentionally
        uses concrete repositories. Future reviews should not repeat this suggestion
        unless the architecture has materially changed.
        """,
        "context": "review feedback",
        "tags": ["project:payments-service", "topic:review-feedback"],
    },
]
