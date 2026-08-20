"""
Centralized configuration.

All model names, generation settings, and other configurable
values should live here rather than being hardcoded inside
functions, so the whole app's AI behavior can be tuned from one
place.
"""

import os

# ---- Gemini model ----
# Verify this against the models available to your API key in
# Google AI Studio (https://aistudio.google.com/) before relying
# on it — availability varies by account/tier.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# ---- Generation settings ----
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

# Max automatic function-calling round trips the SDK will make
# in a single turn before giving up (e.g. tool -> tool -> tool
# -> final answer). Prevents infinite tool-call loops.
MAX_TOOL_CALL_TURNS = 5

# ---- Retry settings ----
# Applies to transient Gemini API failures (rate limits, 5xx
# server errors) — NOT to bad requests or auth failures, which
# won't succeed no matter how many times they're retried.
MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 1.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# ---- App-level defaults ----
# No auth system yet (Day 9+ candidate); every recipe/tool call
# is scoped to this fixed user until accounts are implemented.
DEFAULT_USER_ID = 1