"""
Cooking agent service.

Wraps a Gemini chat session configured with:
- The system prompt (persona + tool-usage guidance)
- The agent-facing tools (automatic function calling)
- Langfuse tracing (via src.observability)
- Retry logic for transient API failures

Automatic function calling means we hand the SDK real Python
functions and it handles: deciding when to call them, executing
them, feeding results back to the model, and looping until the
model produces a final text answer. We don't manually parse
function-call responses.
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
    """A stateful chat session with the cooking assistant."""

    def __init__(self):
        load_dotenv()

        # Set up tracing before creating any client/chat so the
        # instrumentor is active for every call this agent makes.
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
        """
        Send a user message to the agent and return its text
        response. Tool calls the model decides to make happen
        automatically before this returns.

        Retries on transient API errors (rate limits, 5xx server
        errors) with exponential backoff. Non-transient errors
        (bad request, auth failure) fail immediately since retrying
        them can't help.
        """
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.chat.send_message(message)
                return response.text

            except errors.APIError as e:
                last_error = e

                if e.code not in RETRYABLE_STATUS_CODES:
                    # Not a transient failure — retrying won't help.
                    return self._friendly_error(e)

                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY_SECONDS * (2 ** attempt)
                    time.sleep(delay)

            except Exception as e:
                # Non-API errors (network issues, etc.) — still
                # worth a couple of retries.
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