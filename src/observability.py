"""
Langfuse tracing setup.

Uses OpenInference's instrumentor so every Gemini call (including tool
round trips) gets traced automatically - no manual wrapping needed.
Call setup_observability() once when the agent starts; safe to call
again, it just no-ops.
"""

import os

_initialized = False


def setup_observability() -> bool:
    """Returns True if tracing is on, False if it got skipped (e.g. no
    keys set). Either way the app should keep working."""
    global _initialized

    if _initialized:
        return True

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        print(
            "[observability] LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY "
            "not set — Gemini calls will not be traced."
        )
        return False

    try:
        from langfuse import get_client
        from openinference.instrumentation.google_genai import (
            GoogleGenAIInstrumentor,
        )

        # get_client() has to run first - it sets up the tracer that the
        # instrumentor attaches to. Wrong order and traces just vanish.
        langfuse = get_client()

        if not langfuse.auth_check():
            print(
                "[observability] Langfuse auth failed — check "
                "LANGFUSE_PUBLIC_KEY/SECRET_KEY and LANGFUSE_HOST."
            )
            return False

        GoogleGenAIInstrumentor().instrument()
        _initialized = True
        return True

    except Exception as e:
        print(f"[observability] Failed to initialize Langfuse tracing: {e}")
        return False
