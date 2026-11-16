"""
Automated tests (no internet and no API key needed).

Run from the project folder with:
    python -m unittest discover -s tests -v

A "fake" Gemini client is used, so these tests check OUR logic:
memory, context trimming, clearing and error handling.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from google.genai import errors

import utils
from chatbot import ChatbotError, SmartChatbot


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    """Pretends to be client.models. Records what it was sent."""

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def generate_content(self, model, contents, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.error:
            raise self.error
        return FakeResponse(f"reply #{len(self.calls)}")


class FakeClient:
    def __init__(self, error=None):
        self.models = FakeModels(error)


class FakeAPIError(errors.APIError):
    """Builds an APIError without needing a real HTTP response."""

    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def make_bot(error=None, max_messages=10):
    client = FakeClient(error)
    bot = SmartChatbot(api_key="fake-key", client=client, max_context_messages=max_messages)
    return bot, client


def sent_texts(call):
    return [part.text for content in call["contents"] for part in content.parts]


class MemoryTests(unittest.TestCase):
    def test_1_normal_question_gets_reply(self):
        bot, _ = make_bot()
        self.assertEqual(bot.send_message("What is Python?"), "reply #1")

    def test_2_name_is_remembered_in_later_request(self):
        bot, client = make_bot()
        bot.send_message("My name is Abinaya.")
        bot.send_message("What is my name?")
        last = client.models.calls[-1]
        self.assertIn("My name is Abinaya.", sent_texts(last))
        self.assertIn("Abinaya", last["config"].system_instruction)

    def test_3_followup_includes_previous_answer(self):
        bot, client = make_bot()
        bot.send_message("What is an API?")
        bot.send_message("Explain that more simply.")
        self.assertIn("reply #1", sent_texts(client.models.calls[-1]))

    def test_4_history_is_maintained(self):
        bot, _ = make_bot()
        for i in range(3):
            bot.send_message(f"message {i}")
        self.assertEqual(len(bot.history), 6)  # 3 user + 3 model
        self.assertEqual(bot.history[0]["role"], "user")

    def test_5_context_window_limit(self):
        bot, client = make_bot(max_messages=10)
        bot.send_message("My name is Abinaya.")
        for i in range(12):
            bot.send_message(f"filler {i}")
        for call in client.models.calls:
            self.assertLessEqual(len(call["contents"]), 10)
        self.assertEqual(client.models.calls[-1]["contents"][0].role, "user")
        self.assertGreater(bot.removed_count, 0)
        # The oldest message is gone from the window, but the fact is preserved:
        self.assertNotIn("My name is Abinaya.", sent_texts(client.models.calls[-1]))
        self.assertIn("Abinaya", client.models.calls[-1]["config"].system_instruction)

    def test_8_clear_forgets_everything(self):
        bot, client = make_bot()
        bot.send_message("My name is Abinaya.")
        bot.clear()
        bot.send_message("What is my name?")
        last = client.models.calls[-1]
        self.assertEqual(sent_texts(last), ["What is my name?"])
        self.assertNotIn("Abinaya", last["config"].system_instruction)

    def test_failed_call_does_not_change_memory(self):
        bot, client = make_bot()
        bot.send_message("hello")
        client.models.error = httpx.ConnectError("no internet")
        with self.assertRaises(ChatbotError):
            bot.send_message("this will fail")
        self.assertEqual(len(bot.history), 2)

    def test_empty_message_rejected(self):
        bot, _ = make_bot()
        with self.assertRaises(ChatbotError):
            bot.send_message("   ")


class ErrorTests(unittest.TestCase):
    def kind_for(self, error):
        bot, _ = make_bot(error=error)
        with self.assertRaises(ChatbotError) as ctx:
            bot.send_message("hi")
        return ctx.exception.kind

    def test_6_invalid_api_key(self):
        err = FakeAPIError(400, "API key not valid. Please pass a valid API key.")
        self.assertEqual(self.kind_for(err), "invalid_key")

    def test_7_network_failure(self):
        self.assertEqual(self.kind_for(httpx.ConnectError("down")), "connection")

    def test_7_timeout(self):
        self.assertEqual(self.kind_for(httpx.ReadTimeout("slow")), "timeout")

    def test_rate_limit(self):
        self.assertEqual(self.kind_for(FakeAPIError(429, "quota exceeded")), "rate_limit")

    def test_server_error(self):
        self.assertEqual(self.kind_for(FakeAPIError(503, "overloaded")), "server_error")

    def test_missing_key(self):
        with self.assertRaises(ChatbotError) as ctx:
            SmartChatbot(api_key="")
        self.assertEqual(ctx.exception.kind, "missing_key")


class UtilsTests(unittest.TestCase):
    def test_trim_keeps_latest(self):
        history = [{"role": "user" if i % 2 == 0 else "model", "content": str(i)} for i in range(15)]
        kept, removed = utils.trim_history(history, 10)
        self.assertLessEqual(len(kept), 10)
        self.assertEqual(kept[0]["role"], "user")
        self.assertEqual(len(kept) + len(removed), 15)

    def test_fact_extraction(self):
        facts = utils.extract_key_facts("Hi! My name is Abinaya and I live in Chennai.")
        self.assertIn("The user's name is Abinaya.", facts)
        self.assertIn("The user lives in Chennai.", facts)


if __name__ == "__main__":
    unittest.main()
