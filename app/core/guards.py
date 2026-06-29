"""Prompt-injection guards (Phase 21).

Log content is UNTRUSTED user input. Before it reaches the LLM we:
  1. cap its length (stops huge payloads / token blowup), and
  2. neutralize common prompt-injection phrases.
This is defense-in-depth, not a silver bullet — we also delimit/label the data
in the prompts and instruct the model to treat it as data, not instructions.
"""

import re

MAX_PROMPT_CHARS = 8000

# Common prompt-injection phrasings to neutralize.
_INJECTION_PATTERNS = re.compile(
    r"ignore\s+(all\s+|the\s+)?(previous|above)\s+instructions"
    r"|disregard\s+(the\s+|all\s+)?(above|previous)"
    r"|forget\s+(everything|all)\s+"
    r"|system\s*prompt"
    r"|you\s+are\s+now\s+",
    re.IGNORECASE,
)


def sanitize_for_prompt(text: str) -> str:
    """Cap length and filter injection phrases from untrusted text."""
    if not text:
        return text
    text = text[:MAX_PROMPT_CHARS]
    return _INJECTION_PATTERNS.sub("[filtered]", text)
