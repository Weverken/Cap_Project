"""Central place for settings so nothing's hardcoded in the app logic."""

import os

# Double check this model name is still valid in your Google AI Studio
# account before deploying - Google renames/deprecates these often.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

# How many tool calls the model can chain in one turn before it has to
# just answer. Stops it looping forever.
MAX_TOOL_CALL_TURNS = 5

# Only retry on stuff that might actually succeed next time (rate limits,
# server errors). No point retrying a bad request or auth failure.
MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 1.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Fallback user id for anything running outside a logged-in session
# (scripts, tests).
DEFAULT_USER_ID = 1
