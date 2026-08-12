# Security Notes

This project is a hackathon-ready prototype, not a production security certification.

## Current protections

- LLM and Hindsight credentials are environment variables.
- GitHub authentication is optional and never stored in SQLite.
- Review input has a configurable maximum size.
- Hindsight receives compact review outcomes and explicit feedback rather than the full
  raw diff by default.
- CORS is configurable.

## Before production

1. Install a GitHub App with least-privilege permissions.
2. Verify GitHub webhook signatures.
3. Redact secrets from diffs before any LLM or memory call.
4. Add repository-level authorization.
5. Add SSO/RBAC.
6. Encrypt application data at rest.
7. Use a secrets manager.
8. Add rate limits and abuse protection.
9. Add audit logging.
10. Define retention/deletion policies for engineering memory.
11. Treat memory as untrusted input and defend against prompt injection in code/comments.
