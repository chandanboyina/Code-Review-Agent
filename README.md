# Code Review Agent — Memory That Learns Your Engineering Standards

A Hindsight-powered code review agent that learns how a team actually reviews code.

Instead of producing the same generic lint-style advice on every pull request, the agent:

1. Reads a pull request or code diff.
2. Recalls project-specific engineering decisions from **Hindsight**.
3. Reviews the change using those memories plus the current code.
4. Explains which findings are backed by learned team knowledge.
5. Stores review outcomes and developer feedback back into Hindsight.
6. Uses later reviews to avoid rejected suggestions and repeat proven conventions.

> The key demo is **review → feedback → memory → better review**.

## Why this project fits the problem statement

The official problem statement describes a Code Review Agent that learns coding standards, common mistakes, architectural preferences, and past review feedback, then avoids repeating suggestions. This implementation makes that learning loop the center of the product.

The project is deliberately scoped to one professional workflow: **pull-request review**.

## Architecture

```text
                         ┌──────────────────────────┐
                         │      Browser / UI         │
                         │ Review • Memory • Stats   │
                         └────────────┬─────────────┘
                                      │ REST
                                      ▼
                         ┌──────────────────────────┐
                         │       FastAPI API         │
                         │                          │
                         │ Review Orchestrator      │
                         │ GitHub Diff Fetcher      │
                         │ LLM Review Engine        │
                         │ Feedback / Learning      │
                         └───────┬─────────┬────────┘
                                 │         │
                      recall     │         │ retain
                                 ▼         ▼
                         ┌──────────────────────────┐
                         │       Hindsight           │
                         │                          │
                         │ Team Memory Bank         │
                         │ Facts + Observations     │
                         │ Knowledge Graph           │
                         └──────────────────────────┘

                                 │
                                 ▼
                         ┌──────────────────────────┐
                         │        SQLite             │
                         │ Review history            │
                         │ Feedback / audit trail    │
                         └──────────────────────────┘
```

Hindsight is not used as a decorative vector store. The review flow explicitly **recalls before review** and **retains after review/feedback**.

## Features

### 1. PR-aware review
Paste a public GitHub Pull Request URL. The backend fetches the PR metadata and diff.

### 2. Local diff review
Paste a unified diff or source code directly. This is useful for private repositories and the live demo.

### 3. Team memory
Each project gets an isolated Hindsight memory bank.

The bank is configured with a retain mission focused on:
- coding standards
- architectural decisions
- review preferences
- recurring mistakes
- accepted/rejected review feedback

### 4. Memory-aware findings
Every finding can say whether it was:
- `memory_backed`
- `current_code`
- `best_practice`

This makes Hindsight's contribution visible to judges.

### 5. Feedback loop
Reviewers can mark findings:
- accepted
- rejected
- corrected

Optional feedback text is retained as a future engineering memory.

### 6. Before/after learning demo
Use the included seed demo to create team preferences, review once, provide feedback, then review a similar change again.

### 7. Demo mode
The application can run without an LLM key using deterministic review heuristics. This is only a fallback for development. The hackathon demo should use a real LLM + Hindsight.

### 8. Security-conscious defaults
- API keys stay in environment variables.
- GitHub tokens are optional.
- No secrets are sent to Hindsight by the app.
- Review input is bounded by configurable size limits.
- CORS is configurable.
- The UI never exposes server-side credentials.

## Stack

- Python 3.11+
- FastAPI
- Pydantic
- SQLite / SQLAlchemy
- Hindsight
- OpenAI-compatible LLM API (Groq recommended for a fast demo)
- Vanilla HTML/CSS/JavaScript frontend
- Docker Compose

## Hindsight integration

The application uses the official `hindsight-client` package.

The code uses:
- `create_bank`
- `update_bank_config`
- `retain`
- `recall`

The bank mission is intentionally focused on durable engineering knowledge.

## Quick start

### Option A — Docker Compose

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Add your LLM key.

For Groq:

```env
LLM_API_KEY=your_groq_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b

HINDSIGHT_API_LLM_API_KEY=your_groq_key
HINDSIGHT_API_LLM_MODEL=gpt-oss-20b
```

3. Start:

```bash
docker compose up --build
```

4. Open:

```text
http://localhost:8000
```

Hindsight UI:

```text
http://localhost:9999
```

FastAPI docs:

```text
http://localhost:8000/docs
```

### Option B — Run Hindsight separately

Start Hindsight using the official Docker image, then run the backend locally.

```bash
docker run --rm -it --pull always \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=YOUR_LLM_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-oss-20b \
  -v hindsight-data:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

Then:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment variables

See `.env.example`.

Important values:

| Variable | Purpose |
|---|---|
| `HINDSIGHT_API_URL` | Hindsight server URL |
| `HINDSIGHT_API_KEY` | Hindsight Cloud key, if using Cloud |
| `LLM_API_KEY` | LLM key for review generation |
| `LLM_BASE_URL` | OpenAI-compatible endpoint |
| `LLM_MODEL` | Review model |
| `GITHUB_TOKEN` | Optional GitHub token |
| `DEMO_MODE` | Force deterministic demo mode |
| `MAX_DIFF_CHARS` | Input safety limit |

## Winning demo flow

Do not start by explaining the architecture.

### Scene 1 — The problem

Say:

> "A generic reviewer sees this code for the first time. It gives reasonable advice, but it doesn't know how our team actually builds services."

Show a review with generic suggestions.

### Scene 2 — Teach the agent

Use the feedback panel:

```text
Reject: "Introduce a repository interface."

Reason:
"Our service intentionally uses concrete repositories.
We only introduce interfaces at external boundaries."

Accept:
"Validate payment amount before processing."
```

Submit the feedback.

### Scene 3 — Show memory

Open the Memory panel.

Show that Hindsight has retained the engineering decision.

### Scene 4 — Review a similar PR

Submit another change containing the same architectural pattern.

The new review should say something like:

```text
Not flagged:
Repository abstraction

Reason:
Team memory says this service intentionally uses concrete
repositories and interfaces are only introduced at boundaries.
```

Then show a genuinely useful finding that matches the team's standards.

### Scene 5 — The punchline

> "The first review knew software engineering. The second review knew our engineering."

That is the product.

## Suggested seeded scenario

The included demo seed creates these memories:

1. The payments service uses concrete repositories internally.
2. Interfaces are introduced only at external boundaries.
3. Money values must be validated before processing.
4. Controller validation should be thin; business validation belongs in the service.
5. Exceptions should use the project's domain exception hierarchy.
6. Developers rejected a generic repository-abstraction suggestion.

This creates a visible before/after story.

## API

### Health

```http
GET /api/health
```

### Review

```http
POST /api/reviews
Content-Type: application/json
```

Example:

```json
{
  "project": "payments-service",
  "language": "Java",
  "pr_url": "",
  "diff": "diff --git ...",
  "reviewer": "demo-user"
}
```

### Feedback

```http
POST /api/reviews/{review_id}/feedback
```

Example:

```json
{
  "finding_id": "F-001",
  "decision": "rejected",
  "comment": "We intentionally avoid interfaces inside this module."
}
```

### Seed demo memory

```http
POST /api/demo/seed
```

### Memory recall

```http
GET /api/memory?project=payments-service&q=repository
```

### Statistics

```http
GET /api/stats?project=payments-service
```

## Testing

```bash
cd backend
pytest -q
```

The tests cover:
- health endpoint
- deterministic review fallback
- GitHub URL parsing
- memory query construction
- feedback validation

## Project structure

```text
CodeReviewAgent/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── github_service.py
│   │   ├── hindsight_service.py
│   │   ├── llm_service.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── prompts.py
│   │   ├── review_engine.py
│   │   └── schemas.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/
├── data/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Notes on production hardening

For a production deployment, add:
- GitHub App authentication instead of broad personal tokens
- webhook-driven PR events
- repository-level authorization
- secret scanning / redaction before memory retention
- background jobs for large diffs
- Postgres instead of SQLite
- SSO/RBAC
- audit logging
- rate limiting
- signed GitHub webhook verification

The current project intentionally keeps the core workflow compact enough to demonstrate clearly.

## License

MIT
