"""Chapter 2: chat with the plain-text travel agent in your terminal.

    uv run travel-cli
"""

from __future__ import annotations

import asyncio
import os
import sys

from agents import Runner, SQLiteSession

from .agent import build_agent


async def _repl() -> None:
    agent = build_agent(ui=False)
    session = SQLiteSession("cli")  # in-memory conversation history
    print("Wanderly travel planner. Try: 'Prepare me an itinerary for 7 nights and 8 days in Thailand'")
    print("Type 'exit' to quit.\n")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text.lower() in {"exit", "quit"}:
            return
        if not text:
            continue
        result = await Runner.run(agent, text, session=session)
        print(f"\nwanderly> {result.final_output}\n")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set. Copy agent/.env.example to agent/.env and add your key.")
    asyncio.run(_repl())


if __name__ == "__main__":
    main()
