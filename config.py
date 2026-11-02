"""Configuration loaded from environment / .env."""
import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


# Telegram
API_ID = _int("TG_API_ID", 0)
API_HASH = os.getenv("TG_API_HASH", "").strip()
PHONE = os.getenv("TG_PHONE", "").strip() or None
SESSION_NAME = os.getenv("TG_SESSION", "scambait").strip()

# Review channel (optional)
REVIEW_CHAT = os.getenv("REVIEW_CHAT", "").strip() or None

# Behaviour
MODE = os.getenv("MODE", "dry_run").strip().lower()  # dry_run | live
MAX_BAIT_TURNS = _int("MAX_BAIT_TURNS", 8)
MIN_REPLY_DELAY = _int("MIN_REPLY_DELAY", 25)

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "canned").strip().lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
BAIT_PERSONA = os.getenv(
    "BAIT_PERSONA",
    "a friendly but easily-confused person who is interested but keeps "
    "misunderstanding details and asking simple questions",
).strip()

DB_PATH = os.getenv("DB_PATH", "scambait.db").strip()


def validate() -> list[str]:
    """Return a list of fatal config problems."""
    problems = []
    if not API_ID:
        problems.append("TG_API_ID is not set")
    if not API_HASH:
        problems.append("TG_API_HASH is not set")
    if MODE not in ("dry_run", "live"):
        problems.append(f"MODE must be dry_run or live, got {MODE!r}")
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        problems.append("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty")
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        problems.append("LLM_PROVIDER=openai but OPENAI_API_KEY is empty")
    return problems
