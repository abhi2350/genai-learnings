from mcp.server.fastmcp import FastMCP
from reviewer import review_pr, review_code

mcp = FastMCP("code-reviewer")


@mcp.tool()
def review_github_pr(pr_url: str, github_token: str = "") -> dict:
    """Review a GitHub Pull Request and return a structured report with issues, score, and approval status.

    Args:
        pr_url: Full GitHub PR URL, e.g. https://github.com/owner/repo/pull/42
        github_token: Personal access token for private repos (leave empty for public repos)
    """
    result = review_pr(pr_url, github_token or None)
    return result.model_dump()


@mcp.tool()
def review_code_snippet(code: str, language: str = "auto") -> dict:
    """Review a code snippet for bugs, security vulnerabilities, performance issues, and style problems.

    Args:
        code: The source code to review
        language: Programming language (e.g. python, javascript). Use 'auto' to detect automatically.
    """
    result = review_code(code, language)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
