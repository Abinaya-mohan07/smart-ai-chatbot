"""
utils.py
--------
Small helper functions used by chatbot.py.

Everything here is plain Python (no API calls), which makes it easy to read
and easy to test.

A "message" in this project is a dictionary like:
    {"role": "user",  "content": "My name is Abinaya."}
    {"role": "model", "content": "Nice to meet you, Abinaya!"}
Gemini calls the AI's role "model" (not "assistant").
"""

import re
from typing import Dict, List, Tuple

Message = Dict[str, str]

# ---------------------------------------------------------------------------
# 1. Key-fact extraction (keeps important info even after old messages are cut)
# ---------------------------------------------------------------------------
# Each entry: (regular expression, sentence template).
# The regex "captures" the useful part; the template builds a clean fact.
_FACT_PATTERNS = [
    (r"\bmy name is ([A-Za-z][A-Za-z'\-]{1,30})", "The user's name is {}."),
    (r"\bcall me ([A-Za-z][A-Za-z'\-]{1,30})", "The user wants to be called {}."),
    (r"\bi(?:'m| am) from ([^.,!?\n]{2,40})", "The user is from {}."),
    (r"\bi live in ([^.,!?\n]{2,40})", "The user lives in {}."),
    (r"\bi work (?:as|at|for) ([^.,!?\n]{2,40})", "The user works as/at {}."),
    (r"\bi(?:'m| am) studying ([^.,!?\n]{2,40})", "The user is studying {}."),
    (r"\bi (?:like|love|enjoy) ([^.,!?\n]{2,40})", "The user likes {}."),
    (r"\bmy favou?rite ([A-Za-z ]{2,20}) is ([^.,!?\n]{2,40})",
     "The user's favourite {} is {}."),
]


def extract_key_facts(text: str) -> List[str]:
    """Find simple personal facts in a user message (name, city, likes...)."""
    facts: List[str] = []
    for pattern, template in _FACT_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            parts = [group.strip() for group in match.groups()]
            facts.append(template.format(*parts))
    return facts


def merge_facts(existing: List[str], new: List[str], max_facts: int = 20) -> List[str]:
    """Add new facts to the list without duplicates; keep only the newest few."""
    merged = list(existing)
    lowered = [fact.lower() for fact in merged]
    for fact in new:
        if fact.lower() not in lowered:
            merged.append(fact)
            lowered.append(fact.lower())
    return merged[-max_facts:]


# ---------------------------------------------------------------------------
# 2. Context window trimming
# ---------------------------------------------------------------------------
def trim_history(history: List[Message], max_messages: int) -> Tuple[List[Message], List[Message]]:
    """
    Keep only the most recent `max_messages` messages.

    Returns two lists:
        kept    -> messages that will be sent to the API
        removed -> older messages that were cut off (oldest first)

    Gemini expects a conversation to begin with a USER message, so if the cut
    leaves an AI message at the start, that one is removed too.
    """
    if max_messages < 1:
        raise ValueError("max_messages must be at least 1")

    if len(history) <= max_messages:
        return list(history), []

    split_point = len(history) - max_messages
    removed = list(history[:split_point])
    kept = list(history[split_point:])

    while kept and kept[0]["role"] != "user":
        removed.append(kept.pop(0))

    return kept, removed


# ---------------------------------------------------------------------------
# 3. Prompt-building helpers
# ---------------------------------------------------------------------------
def build_system_instruction(base_prompt: str, key_facts: List[str], summary: str) -> str:
    """
    Combine the base system prompt with the preserved context.
    This text is sent with EVERY request, so it never gets removed.
    """
    sections = [base_prompt.strip()]

    if key_facts:
        facts_text = "\n".join(f"- {fact}" for fact in key_facts)
        sections.append("Important facts remembered about the user:\n" + facts_text)

    if summary:
        sections.append("Summary of the earlier part of this conversation:\n" + summary)

    return "\n\n".join(sections)


def format_transcript(messages: List[Message]) -> str:
    """Turn a list of messages into readable text (used for summarization)."""
    lines = []
    for message in messages:
        speaker = "User" if message["role"] == "user" else "Assistant"
        lines.append(f"{speaker}: {message['content']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Input helpers
# ---------------------------------------------------------------------------
def clean_user_input(text: str) -> str:
    """Remove extra spaces/blank lines at the start and end of the message."""
    return (text or "").strip()
