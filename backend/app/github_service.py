import re
from urllib.parse import urlparse
import requests
from .config import get_settings


PR_RE = re.compile(r"^/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    parsed = urlparse(url.strip())
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Only github.com pull request URLs are supported.")
    match = PR_RE.match(parsed.path)
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/org/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pull_request(url: str) -> tuple[str, dict]:
    settings = get_settings()
    owner, repo, number = parse_pr_url(url)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "code-review-agent/1.0",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    response = requests.get(api_url, headers=headers, timeout=20)
    response.raise_for_status()
    metadata = response.json()

    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    diff_response = requests.get(
        diff_url,
        headers={**headers, "Accept": "application/vnd.github.v3.diff"},
        timeout=30,
    )
    diff_response.raise_for_status()

    return diff_response.text, {
        "title": metadata.get("title", ""),
        "state": metadata.get("state", ""),
        "base": metadata.get("base", {}).get("ref", ""),
        "head": metadata.get("head", {}).get("ref", ""),
        "files_changed": metadata.get("changed_files", 0),
        "additions": metadata.get("additions", 0),
        "deletions": metadata.get("deletions", 0),
        "html_url": metadata.get("html_url", url),
    }
