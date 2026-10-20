import os

MODEL = "gemini-3.5-flash-lite"
MAX_CODE_CHARS = 100000

PROMPT = """You are a code documentation assistant.
Write clear documentation for the {language} code below.

Use this plain-text format (no markdown symbols like ** or #):

Overview:
<2-3 sentences on what the code does>

Functions:
- name(parameters): what it does, what it returns (write "None" if there are none)

Classes:
- name: what it represents (write "None" if there are none)

Notes:
<1-3 short, useful observations about the code, if any>

Only describe what is actually in the code. Do not invent behavior.

Code:
{code}
"""


def _friendly_error(exc):
    """Turn a raw error into a short message that is safe to show."""
    text = str(exc).lower()

    if "429" in text or "quota" in text or "resource_exhausted" in text or (
        "rate" in text and "limit" in text
    ):
        return "The free AI limit was reached. Try again in a little while."

    if (
        "api key" in text or "api_key" in text or "401" in text
        or "403" in text or "permission" in text or "unauthenticated" in text
    ):
        return "The AI key was rejected. Check that GEMINI_API_KEY is correct."

    if (
        "timeout" in text or "timed out" in text or "connect" in text
        or "network" in text or "resolve" in text
    ):
        return "Could not reach the AI service. Check your internet connection."

    return "The AI service returned an error."


def generate_ai_documentation_with_note(code, language="Python"):
    """Return (documentation, note).

    documentation is None when the AI could not be used.
    note is a short message explaining why, or a warning (for example
    that long code was cut), or None when everything went normally.
    """
    if not code or not code.strip():
        return None, None

    if not os.environ.get("GEMINI_API_KEY"):
        return None, "AI documentation is off because no API key is set."

    try:
        from google import genai
    except ImportError:
        return None, (
            "AI documentation is off because the google-genai "
            "library is not installed."
        )

    note = None
    sent = code

    if len(code) > MAX_CODE_CHARS:
        # Cut at a line boundary so the AI never sees half a line
        sent = code[:MAX_CODE_CHARS].rsplit("\n", 1)[0]
        note = (
            f"The code is long, so only the first {len(sent.splitlines())} "
            "lines were sent to the AI."
        )

    try:
        client = genai.Client()
        interaction = client.interactions.create(
            model=MODEL,
            input=PROMPT.format(language=language, code=sent),
        )
        text = (interaction.output_text or "").strip()
    except Exception as exc:
        # The full error goes to the terminal only, never to the page
        print(f"[ai_docs] AI documentation failed: {exc}")
        return None, _friendly_error(exc)

    if not text:
        return None, "The AI returned an empty answer."

    return text, note


def generate_ai_documentation(code, language="Python"):
    """Older helper: returns just the documentation text, or None."""
    text, _ = generate_ai_documentation_with_note(code, language)
    return text