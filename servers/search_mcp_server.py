"""MCP server exposing DuckDuckGo search tools."""
from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS

mcp = FastMCP("duckduckgo-search")


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web with DuckDuckGo and return text results.

    Args:
        query: search query
        max_results: number of results to return (1..10)
    """
    max_results = max(1, min(int(max_results), 10))
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."

    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(
            f"[{i}] {r.get('title','').strip()}\n"
            f"{r.get('body','').strip()}\n"
            f"URL: {r.get('href','').strip()}"
        )
    return "\n\n".join(blocks)


@mcp.tool()
def news_search(query: str, max_results: int = 5) -> str:
    """Search news with DuckDuckGo News."""
    max_results = max(1, min(int(max_results), 10))
    with DDGS() as ddgs:
        results = list(ddgs.news(query, max_results=max_results))
    if not results:
        return "No news found."

    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(
            f"[{i}] {r.get('title','').strip()}\n"
            f"{r.get('body','').strip()}\n"
            f"Source: {r.get('source','').strip()}  |  Date: {r.get('date','').strip()}"
        )
    return "\n\n".join(blocks)


if __name__ == "__main__":
    mcp.run()
