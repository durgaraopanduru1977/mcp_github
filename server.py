from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastmcp import FastMCP
from dotenv import load_dotenv
import os
import sys
import httpx

# Load environment variables (GITHUB_TOKEN, GITHUB_OWNER, ...) from a .env file
# sitting next to this script, so the server works regardless of how it's launched.
# override=True ensures the .env value wins over any stale/invalid var already in
# the OS environment; the explicit path makes loading independent of the cwd.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

mcp = FastMCP("durga_mcp_server")

print("Starting MCP server...", file=sys.stderr)

# ---------------------------------------------------------------------------
# GitHub configuration
# ---------------------------------------------------------------------------
GITHUB_API = "https://api.github.com"
# Default account these tools operate against when a bare repo name is given.
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "durgaraopanduru1977")


def _github_client() -> httpx.Client:
    """Return an httpx client preconfigured for the GitHub REST API.

    Reads a Personal Access Token from the GITHUB_TOKEN env var. The token is
    optional for reading public repos, but required for private repos, higher
    rate limits, and any write action (e.g. creating issues).
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(base_url=GITHUB_API, headers=headers, timeout=30.0)


def _full_name(repo: str) -> str:
    """Accept either 'repo' (assumes the default owner) or 'owner/repo'."""
    return repo if "/" in repo else f"{GITHUB_OWNER}/{repo}"

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool()
def sub(a: int,b: int) -> int: 
    return a - b

@mcp.tool()
def mul(a: int,b: int) -> int: 
    return a * b

@mcp.tool()
def divide(a: int,b: int) -> int: 
    return a / b

# ---------------------------------------------------------------------------
# GitHub tools
# ---------------------------------------------------------------------------
@mcp.tool()
def list_my_repos(per_page: int = 30) -> list[dict]:
    """List repositories for the configured GitHub account (durgaraopanduru1977).

    With a GITHUB_TOKEN set, lists the authenticated user's own repos
    (including private). Without a token, lists that user's public repos only.
    """
    with _github_client() as client:
        if os.environ.get("GITHUB_TOKEN"):
            resp = client.get(
                "/user/repos",
                params={"per_page": per_page, "sort": "updated", "affiliation": "owner"},
            )
        else:
            resp = client.get(
                f"/users/{GITHUB_OWNER}/repos",
                params={"per_page": per_page, "sort": "updated"},
            )
        resp.raise_for_status()
        return [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "private": r["private"],
                "description": r["description"],
                "language": r["language"],
                "stars": r["stargazers_count"],
                "open_issues": r["open_issues_count"],
                "url": r["html_url"],
                "updated_at": r["updated_at"],
            }
            for r in resp.json()
        ]


@mcp.tool()
def get_repo(repo: str) -> dict:
    """Get details for a repository.

    `repo` may be a bare name (e.g. "my-project", assumes the default owner)
    or a full "owner/name".
    """
    with _github_client() as client:
        resp = client.get(f"/repos/{_full_name(repo)}")
        resp.raise_for_status()
        r = resp.json()
        return {
            "full_name": r["full_name"],
            "private": r["private"],
            "description": r["description"],
            "default_branch": r["default_branch"],
            "language": r["language"],
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "open_issues": r["open_issues_count"],
            "url": r["html_url"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }


@mcp.tool()
def list_issues(
    repo: str, state: str = "open", kind: str = "all", per_page: int = 30
) -> list[dict]:
    """List issues and/or pull requests for a repository.

    Args:
        repo: bare name (assumes default owner) or "owner/name".
        state: "open", "closed", or "all".
        kind: "issues", "prs", or "all" (GitHub returns PRs via the issues API).
    """
    with _github_client() as client:
        resp = client.get(
            f"/repos/{_full_name(repo)}/issues",
            params={"state": state, "per_page": per_page},
        )
        resp.raise_for_status()
        out = []
        for i in resp.json():
            is_pr = "pull_request" in i
            if kind == "issues" and is_pr:
                continue
            if kind == "prs" and not is_pr:
                continue
            out.append(
                {
                    "number": i["number"],
                    "type": "pr" if is_pr else "issue",
                    "title": i["title"],
                    "state": i["state"],
                    "user": i["user"]["login"],
                    "comments": i["comments"],
                    "url": i["html_url"],
                    "created_at": i["created_at"],
                }
            )
        return out


@mcp.tool()
def create_issue(repo: str, title: str, body: str = "") -> dict:
    """Create a new issue in a repository. Requires GITHUB_TOKEN with write scope.

    `repo` may be a bare name (assumes default owner) or "owner/name".
    """
    if not os.environ.get("GITHUB_TOKEN"):
        raise ValueError("GITHUB_TOKEN env var is required to create issues.")
    with _github_client() as client:
        resp = client.post(
            f"/repos/{_full_name(repo)}/issues",
            json={"title": title, "body": body},
        )
        resp.raise_for_status()
        r = resp.json()
        return {
            "number": r["number"],
            "title": r["title"],
            "state": r["state"],
            "url": r["html_url"],
        }


@mcp.resource("demo://greeting/{name}")
def greeting(name: str) -> str:
    return f"Hello, {name}!"

@mcp.prompt()
def summarize(topic: str) -> str:
    return f"Write a 3-sentence summary of: {topic}"

if __name__ == "__main__":
    mcp.run(transport="stdio")