"""
chatbot.py
----------
The "brain" of the project. It:
  * connects to the Google Gemini API (Google Gen AI SDK: `google-genai`),
  * remembers the conversation (multi-turn memory),
  * limits how much history is sent (context window management),
  * turns scary API/network errors into friendly messages.

You can also test it WITHOUT Streamlit:  python chatbot.py
"""

from typing import Dict, List, Optional

import httpx
from google import genai
from google.genai import errors, types

import config
import utils


class ChatbotError(Exception):
    """
    One simple error type for the whole app.

    user_message -> friendly text that can be shown on screen
    kind         -> short label such as "invalid_key" or "rate_limit"
    """

    def __init__(self, user_message: str, kind: str = "unknown"):
        super().__init__(user_message)
        self.user_message = user_message
        self.kind = kind


class SmartChatbot:
    """A chatbot object holds ONE conversation (its memory lives inside it)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_context_messages: Optional[int] = None,
        enable_summary: Optional[bool] = None,
        client=None,
    ):
        self.api_key = (api_key if api_key is not None else config.GEMINI_API_KEY).strip()
        self.model = model or config.MODEL_NAME
        self.max_context_messages = max_context_messages or config.MAX_CONTEXT_MESSAGES
        self.enable_summary = config.ENABLE_SUMMARY if enable_summary is None else enable_summary

        # ----- memory -----
        self.history: List[Dict[str, str]] = []   # messages that are kept in context
        self.key_facts: List[str] = []            # important facts (e.g. user's name)
        self.summary: str = ""                    # optional AI summary of removed messages
        self.removed_count: int = 0               # how many old messages were cut off

        # `client` can be injected for testing; normally we build the real one.
        if client is not None:
            self.client = client
        else:
            self.client = self._create_client()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _create_client(self):
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ChatbotError(
                "No Gemini API key found. Open the .env file, set "
                "GEMINI_API_KEY=your real key, save it and restart the app.",
                kind="missing_key",
            )
        try:
            # timeout is in MILLISECONDS in the SDK
            return genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=config.REQUEST_TIMEOUT_SECONDS * 1000),
            )
        except Exception as exc:  # noqa: BLE001
            raise self._translate_error(exc) from exc

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def send_message(self, user_text: str) -> str:
        """
        Send one user message and return the AI's reply.

        Steps:
          1. add the user message to a temporary history
          2. trim it to the latest N messages (context window)
          3. optionally summarize the removed messages
          4. call Gemini with system prompt + preserved facts + trimmed history
          5. ONLY if it works, save everything to memory
        """
        text = utils.clean_user_input(user_text)
        if not text:
            raise ChatbotError("Please type a message first.", kind="empty_input")
        if len(text) > config.MAX_INPUT_CHARS:
            raise ChatbotError(
                f"Your message is too long ({len(text)} characters). "
                f"Please keep it under {config.MAX_INPUT_CHARS}.",
                kind="too_long",
            )

        # 1 + 2: add the new message and trim
        pending = self.history + [{"role": "user", "content": text}]
        window, removed = utils.trim_history(pending, self.max_context_messages)

        # Remember important facts from this message (name, city, likes, ...)
        new_facts = utils.merge_facts(self.key_facts, utils.extract_key_facts(text))

        # 3: optional summary of removed messages
        new_summary = self.summary
        if removed and self.enable_summary:
            new_summary = self._summarize(removed, self.summary)

        # 4: call the API
        system_instruction = utils.build_system_instruction(
            config.SYSTEM_PROMPT, new_facts, new_summary
        )
        reply = self._generate(window, system_instruction)

        # 5: success -> commit to memory
        self.history = window + [{"role": "model", "content": reply}]
        self.key_facts = new_facts
        self.summary = new_summary
        self.removed_count += len(removed)
        return reply

    def clear(self) -> None:
        """Forget everything (used by the Clear Chat button)."""
        self.history = []
        self.key_facts = []
        self.summary = ""
        self.removed_count = 0

    def get_stats(self) -> Dict[str, object]:
        """Small report shown in the sidebar."""
        return {
            "messages_in_context": len(self.history),
            "max_context_messages": self.max_context_messages,
            "messages_removed": self.removed_count,
            "key_facts": list(self.key_facts),
            "has_summary": bool(self.summary),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate(self, window: List[Dict[str, str]], system_instruction: str) -> str:
        """Call Gemini and return the reply text."""
        contents = [
            types.Content(role=m["role"], parts=[types.Part(text=m["content"])])
            for m in window
        ]
        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=config.TEMPERATURE,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generation_config,
            )
        except Exception as exc:  # noqa: BLE001
            raise self._translate_error(exc) from exc

        reply = (getattr(response, "text", None) or "").strip()
        if not reply:
            raise ChatbotError(
                "The AI returned an empty answer (it may have been blocked by a "
                "safety filter). Please rephrase your question and try again.",
                kind="empty_response",
            )
        return reply

    def _summarize(self, removed: List[Dict[str, str]], previous_summary: str) -> str:
        """
        ADVANCED FEATURE: ask Gemini to compress removed messages into a short
        summary. If this fails we silently keep the old summary, because the
        main answer is more important than the summary.
        """
        prompt = (
            "Update the running summary of a conversation.\n"
            "Keep it under 120 words. Keep names, facts, decisions and open "
            "questions. Return ONLY the new summary text.\n\n"
            f"Previous summary:\n{previous_summary or '(none)'}\n\n"
            f"Older messages to add:\n{utils.format_transcript(removed)}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            return (getattr(response, "text", None) or "").strip() or previous_summary
        except Exception:  # noqa: BLE001
            return previous_summary

    @staticmethod
    def _translate_error(exc: Exception) -> ChatbotError:
        """Convert any exception into a friendly ChatbotError."""
        if isinstance(exc, ChatbotError):
            return exc

        # --- Errors returned by the Gemini API itself ---
        if isinstance(exc, errors.APIError):
            code = getattr(exc, "code", None)
            details = f"{getattr(exc, 'message', '')} {exc}".lower()

            if "api key" in details or "api_key_invalid" in details or code in (401, 403):
                return ChatbotError(
                    "Your Gemini API key is invalid or not allowed. Check the key in "
                    "your .env file (no spaces or quotes), then restart the app.",
                    kind="invalid_key",
                )
            if code == 429:
                return ChatbotError(
                    "Rate limit reached (too many requests or free quota used up). "
                    "Please wait a minute and try again.",
                    kind="rate_limit",
                )
            if code == 404:
                return ChatbotError(
                    f"The model '{config.MODEL_NAME}' was not found. Change "
                    "GEMINI_MODEL in your .env file to a currently supported model.",
                    kind="model_not_found",
                )
            if code in (500, 502, 503, 504):
                return ChatbotError(
                    "The Gemini service is busy or temporarily unavailable. "
                    "Please try again in a few moments.",
                    kind="server_error",
                )
            return ChatbotError(
                f"The Gemini API rejected the request (code {code}). Please try again.",
                kind="api_error",
            )

        # --- Network problems (order matters: timeout first) ---
        if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
            return ChatbotError(
                "The request timed out. Please check your internet and try again.",
                kind="timeout",
            )
        if isinstance(exc, (httpx.TransportError, ConnectionError, OSError)):
            return ChatbotError(
                "Could not connect to the Gemini API. Please check your internet "
                "connection (or VPN/firewall) and try again.",
                kind="connection",
            )

        return ChatbotError(
            f"Something unexpected went wrong: {type(exc).__name__}. Please try again.",
            kind="unknown",
        )


# ----------------------------------------------------------------------
# Optional terminal mode:  python chatbot.py
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("Smart AI Chatbot (terminal mode). Type 'quit' to exit, 'clear' to reset.\n")
    try:
        bot = SmartChatbot()
    except ChatbotError as error:
        print("Error:", error.user_message)
        raise SystemExit(1)

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("quit", "exit"):
            break
        if user_input.strip().lower() == "clear":
            bot.clear()
            print("Bot: Conversation cleared.\n")
            continue
        try:
            print("Bot:", bot.send_message(user_input), "\n")
        except ChatbotError as error:
            print("Error:", error.user_message, "\n")
