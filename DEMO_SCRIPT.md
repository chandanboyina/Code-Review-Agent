# 3-Minute Winning Demo Script

## 0:00 — Hook

> "Most code reviewers remember nothing. If a developer rejects the same suggestion
> five times, a generic reviewer will happily make it a sixth time."

Open the dashboard.

## 0:15 — Seed memory

Click **Seed team memory**.

Open **What the agent remembers**.

Point out:
- concrete repositories are intentional
- interfaces only at boundaries
- payment amounts must be validated
- controllers stay thin
- domain exceptions are preferred

Say:

> "These aren't generic rules. They're the team's decisions."

## 0:40 — First review

Click **Load demo change**.

Run the review.

Point to the `memory_backed` basis.

Explain:

> "Before reviewing, the agent recalled relevant engineering decisions from Hindsight."

## 1:10 — Teach it

Click **Reject** on an architecture suggestion if one appears.

Comment:

> "We intentionally use concrete repositories in this module. Do not suggest
> introducing an interface unless the boundary changes."

Show the feedback counter increasing.

Refresh memory.

Say:

> "That rejection is now part of the team's memory."

## 1:45 — Second review

Change the demo diff slightly, for example:

```java
private final PaymentRepository repository;

public PaymentService(PaymentRepository repository) {
    this.repository = repository;
}
```

Run another review.

Point out that the agent does not blindly repeat the rejected abstraction suggestion.

## 2:20 — Show the learning loop

Show:

Review 1 → Feedback → Hindsight → Review 2

Then say:

> "The model didn't become smarter. The system became more informed."

## 2:40 — Close

> "That's the difference between an AI code reviewer and a code review system
> that actually learns how your team engineers software."

## Judge questions to prepare for

### Why Hindsight instead of a normal vector database?

Answer:

> "We need more than similarity search. Engineering feedback has entities,
> temporal context, relationships, and durable observations. Hindsight's retain
> and recall model is built around turning interactions into structured memory."

### How does it avoid repeating bad advice?

Answer:

> "Rejected feedback is retained as experience. On later reviews we recall that
> evidence and instruct the reviewer not to repeat it unless the current architecture
> materially differs."

### What is actually learned?

Answer:

> "Coding standards, architectural decisions, rationale, recurring mistakes,
> and accepted or rejected review feedback."

### Is the LLM making decisions blindly?

Answer:

> "No. Findings are required to declare their basis: memory-backed, current-code,
> or generic best practice. The UI exposes that distinction."

### How would this become production software?

Answer:

> "A GitHub App would receive PR webhooks, authorization would scope memories by
> repository, review jobs would run asynchronously, and the audit trail would move
> to Postgres with SSO/RBAC."

## Important

The content guide requires the published article to focus on the project rather than the
hackathon, and says articles should show Hindsight integration, real code, a before/after
example, an honest limitation, and screenshots. Use those requirements when creating the
final submission content.
