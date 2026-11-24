"""Runtime configuration, read from environment variables (and agent/.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Empty string -> let the OpenAI Agents SDK pick its default model.
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    # Model for the scope classifier (guardrail). Empty -> same as OPENAI_MODEL. A small, fast model is ideal.
    guardrail_model: str = os.getenv("GUARDRAIL_MODEL", "")
    host: str = os.getenv("AGENT_HOST", "127.0.0.1")
    port: int = int(os.getenv("AGENT_PORT", "8000"))
    # Comma-separated list of origins allowed to call the API (the Vite dev server).
    cors_origins: tuple[str, ...] = tuple(
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if o.strip()
    )


settings = Settings()
