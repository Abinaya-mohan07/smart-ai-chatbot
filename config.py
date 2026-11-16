"""
config.py
---------
Central place for all settings.

It loads values from the .env file (so the API key is NEVER written in code)
and exposes them as simple Python variables that other files can import.
"""

import os

from dotenv import load_dotenv

# Read the .env file in the project folder and put its values into the
# environment so os.getenv() can find them.
load_dotenv()


def _get_int(name: str, default: int) -> int:
    """Read an integer setting from the environment, falling back safely."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    """Read a decimal setting from the environment, falling back safely."""
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    """Read a True/False setting from the environment."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# API key (comes ONLY from the .env file / environment)
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# If Google retires this model name, just change GEMINI_MODEL in your .env file.
MODEL_NAME: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
TEMPERATURE: float = _get_float("TEMPERATURE", 0.7)
REQUEST_TIMEOUT_SECONDS: int = _get_int("REQUEST_TIMEOUT_SECONDS", 30)

# ---------------------------------------------------------------------------
# Context window management
# ---------------------------------------------------------------------------
# Only the latest N messages (user + AI together) are sent to the API.
MAX_CONTEXT_MESSAGES: int = _get_int("MAX_CONTEXT_MESSAGES", 10)
# Advanced: let the AI summarize messages that fall out of the window.
ENABLE_SUMMARY: bool = _get_bool("ENABLE_SUMMARY", False)
# Safety limit for one user message (characters).
MAX_INPUT_CHARS: int = _get_int("MAX_INPUT_CHARS", 4000)

# ---------------------------------------------------------------------------
# System prompt (the chatbot's personality and rules)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """You are a friendly, helpful and patient AI assistant.

Personality and style:
- Be warm, polite and encouraging, like a good teacher.
- Give clear, simple and accurate answers. Use easy words and short sentences.
- If a topic is complex, explain it step by step and use small examples.
- If you are not sure about something, say so honestly. Never make up facts.

Conversation rules:
- Always follow the conversation context. Use earlier messages to understand
  follow-up questions such as "explain that again" or "what about the second one?".
- Remember personal details the user shares (for example their name) and use
  them naturally when they ask about them later.
- Keep answers focused and not longer than needed.
"""

# ---------------------------------------------------------------------------
# App text
# ---------------------------------------------------------------------------
APP_TITLE: str = "Smart AI Chatbot"
APP_SUBTITLE: str = "A multi-turn chatbot with memory, powered by Google Gemini"
