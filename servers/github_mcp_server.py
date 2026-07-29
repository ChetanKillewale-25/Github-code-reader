"""
MCP server exposing GitHub code-reading tools.
Run standalone OR let agent.py spawn it over stdio.
"""
import os
import base64
from mcp.server.fastmcp import FastMCP
from github import Github

mcp = FastMCP("github-code-reader")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _client() -> Github:
    # Authenticated requests get 5000/hr; unauthenticated only 60/hr.
    return Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()


@mcp.tool()
def list_repo_files(owner: str, repo: str, path: str = "", ref: str = "") -> str:
    """List files/directories at a path inside a GitHub repository.

    Args:
        owner: Repo owner, e.g. "langchain-ai"
        repo:  Repo name, e.g. "langgraph"
        path:  Sub-path inside the repo; "" means root
        ref:   Branch / tag / commit; "" uses default branch
    """
    g = _client()
    r = g.get_repo(f"{owner}/{repo}")
    contents = r.get_contents(path, ref=ref) if ref else r.get_contents(path)

    if isinstance(contents, list):
        lines = [f"{c.type:<5} {c.path}" for c in contents]
        return "\n".join(lines) if lines else "Empty directory."
    return f"{contents.type:<5} {contents.path}"


@mcp.tool()
def read_file_from_repo(owner: str, repo: str, path: str, ref: str = "") -> str:
    """Read the textual content of a file inside a GitHub repository."""
    g = _client()
    r = g.get_repo(f"{owner}/{repo}")
    content = r.get_contents(path, ref=ref) if ref else r.get_contents(path)

    if content.encoding == "base64":
        return base64.b64decode(content.content).decode("utf-8", errors="replace")
    return content.content or ""


@mcp.tool()
def search_repo_code(query: str, owner: str = "", repo: str = "") -> str:
    """Search code on GitHub. Optionally scope to a single repo.

    Args:
        query: code search string
        owner: optional repo owner to restrict the search
        repo:  optional repo name to restrict the search
    """
    g = _client()
    q = f"{query} repo:{owner}/{repo}" if owner and repo else query
    results = g.search_code(q)
    out = [f"{item.repository.full_name} -> {item.path}" for item in results[:10]]
    return "\n".join(out) if out else "No results."


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
