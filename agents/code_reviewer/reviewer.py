import os
import re
from typing import List, Optional

import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
client = Anthropic()


class Issue(BaseModel):
    line: Optional[int]
    severity: str         # "critical", "warning", "suggestion"
    category: str         # "security", "bug", "performance", "style"
    description: str
    fix: str


class CodeReview(BaseModel):
    language: str
    summary: str
    issues: List[Issue]
    overall_score: int    # 1-10
    approved: bool


class FileReview(BaseModel):
    filename: str
    summary: str
    issues: List[Issue]


class PRReview(BaseModel):
    pr_title: str
    pr_url: str
    overall_summary: str
    files_reviewed: int
    file_reviews: List[FileReview]
    critical_issues: int
    overall_score: int    # 1-10
    approved: bool
    review_comment: str   # the comment you'd post on the PR


def review_code(code: str, language: str = "auto") -> CodeReview:
    prompt = f"""Review the following {language} code. Identify all issues including bugs, security vulnerabilities, performance problems, and style issues.

```{language}
{code}
```

Be thorough. Flag anything that could cause problems in production."""

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=4096,
        system="You are a senior software engineer doing a code review. Be precise, practical, and specific about line numbers when possible.",
        messages=[{"role": "user", "content": prompt}],
        output_format=CodeReview,
    )
    return response.parsed_output


def _parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def _fetch_pr(owner: str, repo: str, pr_number: int, token: Optional[str]) -> tuple[dict, list[dict]]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    pr_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        headers=headers,
        timeout=15,
    )
    pr_resp.raise_for_status()

    files_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        headers=headers,
        timeout=15,
    )
    files_resp.raise_for_status()

    return pr_resp.json(), files_resp.json()


def review_pr(pr_url: str, github_token: Optional[str] = None) -> PRReview:
    owner, repo, pr_number = _parse_pr_url(pr_url)
    token = github_token or os.getenv("GITHUB_TOKEN")

    pr_data, files = _fetch_pr(owner, repo, pr_number, token)

    pr_title = pr_data.get("title", "")
    pr_body = pr_data.get("body") or ""
    base_branch = pr_data["base"]["ref"]
    head_branch = pr_data["head"]["ref"]

    file_sections = []
    for f in files:
        patch = f.get("patch", "(binary file or diff not available)")
        file_sections.append(
            f"### {f['filename']} ({f['status']}, +{f['additions']} -{f['deletions']})\n"
            f"```diff\n{patch}\n```"
        )

    prompt = f"""Review this GitHub Pull Request:

**Title:** {pr_title}
**URL:** {pr_url}
**Branch:** `{head_branch}` → `{base_branch}`
**Description:**
{pr_body or "(no description)"}

## Changed Files ({len(files)} files)

{"\\n\\n".join(file_sections)}

Review every changed file thoroughly. Flag bugs, security vulnerabilities, performance issues, and style problems. Reference specific diff lines where possible. Decide if this PR is safe to merge."""

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=8192,
        system="You are a senior software engineer reviewing a GitHub pull request. Be precise, practical, and actionable. Reference specific lines from the diffs.",
        messages=[{"role": "user", "content": prompt}],
        output_format=PRReview,
    )
    return response.parsed_output
