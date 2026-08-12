# Architecture and Memory Design

## Memory is the product primitive

The system has two persistent layers.

### Application database

SQLite stores:
- review history
- review result JSON
- reviewer feedback
- timestamps

This is an audit/application store.

### Hindsight

Hindsight stores:
- team coding standards
- architectural decisions
- review experiences
- accepted/rejected suggestions
- durable observations derived from repeated evidence

This is the agent's long-term engineering memory.

## Review lifecycle

```text
1. Receive PR/diff
       |
       v
2. Normalize + bound input
       |
       v
3. Build memory query
       |
       v
4. Hindsight recall
       |
       v
5. LLM reviews code + recalled memory
       |
       v
6. Store application review
       |
       v
7. Retain compact review outcome
       |
       v
8. Reviewer accepts/rejects/corrects finding
       |
       v
9. Retain feedback
       |
       v
10. Future review recalls feedback
```

## Why compact retention?

The raw diff is not automatically dumped into long-term memory. The application retains
a compact outcome and explicit feedback.

This reduces noisy memories and keeps the memory mission focused on durable engineering
knowledge.

## Memory isolation

Each project gets a Hindsight bank:

```text
code-review-payments-service
code-review-orders-service
code-review-auth-service
```

This prevents project-specific architectural decisions from being mixed conceptually.

## Explainability

Each finding has:

```json
{
  "basis": "memory_backed",
  "memory_refs": [
    "Internal payment modules intentionally use concrete repositories."
  ]
}
```

This is important for the demo because judges can see exactly where memory changed behavior.

## Production evolution

The prototype can be upgraded with:
- GitHub App + webhooks
- repository installation IDs
- RBAC and SSO
- Postgres
- background workers
- secret scanning
- diff redaction
- review comments written directly to GitHub
- metrics for repeated/rejected suggestions
- automated memory quality evaluation
