"""
LangGraph ReAct agent that consumes tools from two MCP servers
(GitHub + DuckDuckGo) and uses Google Gemini (free tier).
"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# --- MODIFIED SECTION ---
# This explicitly tells Python to look for .env in the exact same folder as agent.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")

if not GEMINI_API_KEY:
    # Print the path so you can verify where it is looking
    print(f"DEBUG: Looked for .env at: {BASE_DIR / '.env'}")
    raise SystemExit("Set GEMINI_API_KEY in your .env file (get one free at aistudio.google.com/apikey).")

# Each entry spawns an MCP server as a subprocess and talks to it over stdio.
SERVERS = {
    "github": {
        "command": "python",
        "args":    ["servers/github_mcp_server.py"],
        "transport": "stdio",
        "env": {"GITHUB_TOKEN": GITHUB_TOKEN},
    },
    "duckduckgo": {
        "command": "python",
        "args":    ["servers/search_mcp_server.py"],
        "transport": "stdio",
    },
}

SYSTEM_PROMPT = """You are a senior developer research assistant.

You have two MCP tool sources:
  • GitHub  -> list_repo_files, read_file_from_repo, search_repo_code
  • DuckDuckGo -> web_search, news_search

Operating procedure:
1. When asked about a repo, FIRST list its files, THEN read only the files
   that look relevant. Don't read entire repos blindly.
2. When asked about something external (docs, latest news, library version),
   use DuckDuckGo.
3. Combine code evidence with web evidence when relevant.
4. Always cite:
     - file path  -> owner/repo/path
     - web result -> URL
5. Be concise. Prefer 1 short paragraph + a small code snippet if useful.
"""


async def main() -> None:
    # 1) LLM ---------------------------------------------------------------
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",           # free-tier friendly
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        max_retries=2,
    )

    # 2) Discover MCP tools ------------------------------------------------
    client = MultiServerMCPClient(SERVERS)
    tools  = await client.get_tools()
    print(f"Loaded {len(tools)} MCP tools:")
    for t in tools:
        print(f"  • {t.name}")

    # 3) Build the ReAct agent --------------------------------------------
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

    # 4) REPL --------------------------------------------------------------
    print("\n✅ MCP + LangGraph + Gemini agent ready. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = await agent.ainvoke({"messages": [("user", user_input)]})
        answer = result["messages"][-1].content
        print(f"\nAssistant: {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
