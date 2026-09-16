"""
The cooking agent - basically a Gemini chat session with tools attached.

Handles the system prompt, tool registration, tracing, and retries.
Uses Gemini's automatic function calling, so we just hand it real
Python functions and it figures out when to call them and loops until
it has a final answer. No manual parsing of tool-call responses.
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from langfuse import observe

from src.config import (
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    MAX_TOOL_CALL_TURNS,
    MAX_RETRIES,
    RETRY_BASE_DELAY_SECONDS,
    RETRYABLE_STATUS_CODES,
)
from src.prompts.system_prompt import COOKING_ASSISTANT_SYSTEM_PROMPT
from src.agent.tools import AGENT_TOOLS
from src.observability import setup_observability


class CookingAgent:
    """One chat session with the cooking assistant."""

    def __init__(self):
        load_dotenv()

        # Needs to run before the client is created so tracing catches
        # everything.
        setup_observability()

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables."
            )

        self.client = genai.Client(api_key=api_key)

        self.chat = self.client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=COOKING_ASSISTANT_SYSTEM_PROMPT,
                temperature=GEMINI_TEMPERATURE,
                tools=AGENT_TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=MAX_TOOL_CALL_TURNS,
                ),
            ),
        )

    @observe(name="cooking_agent_message")
    def send_message(self, message: str) -> str:
        """Send a message, get the reply back as text. Any tool calls
        happen automatically in between. Retries a couple times on
        rate limits / server errors; gives up right away on stuff like
        a bad request that won't fix itself."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.chat.send_message(message)
                return response.text

            except errors.APIError as e:
                last_error = e

                if e.code not in RETRYABLE_STATUS_CODES:
                    return self._friendly_error(e)

                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY_SECONDS * (2 ** attempt)
                    time.sleep(delay)

            except Exception as e:
                # network hiccups etc - still worth a retry
                last_error = e

                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY_SECONDS * (2 ** attempt)
                    time.sleep(delay)

        return self._friendly_error(last_error)

    @staticmethod
    def _friendly_error(error: Exception) -> str:
        return (
            "Sorry, something went wrong talking to the assistant "
            f"after retrying: {error}"
        )
