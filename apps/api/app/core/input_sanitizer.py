"""Input sanitization and prompt injection protection.

Sanitizes user-supplied strings, detects common prompt injection patterns,
and validates file uploads.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── Prompt injection patterns ──────────────────────────────────────────
PROMPT_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)\bignore\s+(all\s+)?(previous|above|prior)\s+(instructions|commands|directions|prompts)\b"),
    re.compile(r"(?i)\b(forget|disregard|override)\s+(all\s+)?(previous|above|prior)\b"),
    re.compile(r"(?i)\byou\s+are\s+now\b.*\b(not|instead|pretend|roleplay)\b"),
    re.compile(r"(?i)\b(new\s+)?(system\s+)?prompt:?\s*$", re.MULTILINE),
    re.compile(r"(?i)\b[ds]o\s+not\s+(follow|obey|adhere|comply)\b"),
    re.compile(r"(?i)\b(jailbreak|prompt\s+injection|leak|extract)\s*(prompt|instructions|system)\b"),
    re.compile(r"(?i)reveal\s+(your\s+)?(system\s+)?prompt"),
    re.compile(r"(?i)(role\s*play|roleplay)\s+as\s+"),
    re.compile(r"(?i)output\s+(your\s+)?(raw|original|initial|system)\s+(instructions|prompt|command)"),
]

ALLOWED_FILE_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".pdf",
    ".docx",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def sanitize_string(value: str, max_length: int = 10000) -> str:
    """Strip control characters and limit length."""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return cleaned[:max_length]


def contains_prompt_injection(text: str) -> bool:
    """Check if text contains known prompt injection patterns."""
    return any(pattern.search(text) for pattern in PROMPT_INJECTION_PATTERNS)


class PromptInjectionError(ValueError):
    pass


def sanitize_chat_input(text: str, strict: bool = True) -> str:
    """Sanitize chat/agent input: strip control chars, detect injection."""
    cleaned = sanitize_string(text)
    if contains_prompt_injection(cleaned):
        logger.warning("Prompt injection detected in input: %.100s", cleaned)
        if strict:
            raise PromptInjectionError("Potential prompt injection detected")
    return cleaned


def validate_file_upload(filename: str, content: bytes) -> dict[str, Any]:
    """Validate file upload: extension, size, and basic content safety."""
    import os

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return {"valid": False, "reason": f"File extension '{ext}' is not allowed"}
    if len(content) > MAX_FILE_SIZE_BYTES:
        return {"valid": False, "reason": f"File exceeds {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit"}
    return {"valid": True}


def sanitize_html(text: str) -> str:
    """Minimal XSS protection by escaping HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
