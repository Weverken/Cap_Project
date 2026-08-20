"""
Langfuse observability setup.

Uses OpenInference's Google GenAI instrumentor to automatically
trace every Gemini call made through the google-genai SDK —
including the tool-calling round trips inside automatic function
calling — without needing to manually wrap each call.

Call setup_observability() once, early (e.g. when the agent
service is first created). Calling it more than once is safe;
the underlying instrumentor no-ops if already instrumented.
"""

import os

_initialized = False


def setup_observability() -> bool:
    """
    Initialize Langfuse tracing for Gemini calls.

    Returns True if tracing was set up, False if it was skipped
    (e.g. missing credentials) — the app should keep working
    either way, just without traces.
    """
    global _initialized

    if _initialized:
        return True

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        # Observability is required by the assignment, but the
        # app shouldn't hard-crash in local dev if it's not
        # configured yet — surface this clearly instead.
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

        # IMPORTANT: get_client() must run before instrument().
        # It sets up Langfuse's OpenTelemetry tracer provider/exporter.
        # If the instrumentor runs first, it attaches to whatever
        # (no-op) tracer provider exists at that moment, and Gemini
        # spans silently never reach Langfuse — you'd only see the
        # top-level @observe() span with nothing nested inside it.
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