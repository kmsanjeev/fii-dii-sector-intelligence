from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, urlunparse


PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\bignore (all )?previous instructions\b", re.IGNORECASE),
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\bdeveloper message\b", re.IGNORECASE),
    re.compile(r"\btool permissions\b", re.IGNORECASE),
    re.compile(r"\bexecute command\b", re.IGNORECASE),
]

UNSAFE_SCHEMES = {"file", "javascript", "data", "ftp", "gopher", "chrome", "vscode"}


def normalize_uri(uri: str) -> str:
    parsed = urlparse((uri or "").strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or ""
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def is_safe_uri(uri: str, *, allowed_schemes: set[str] | None = None) -> tuple[bool, str | None]:
    parsed = urlparse((uri or "").strip())
    scheme = parsed.scheme.lower()
    if not scheme:
        return False, "missing_uri_scheme"
    if scheme in UNSAFE_SCHEMES:
        return False, f"unsafe_uri_scheme:{scheme}"
    if allowed_schemes and scheme not in allowed_schemes:
        return False, f"scheme_not_allowed:{scheme}"
    return True, None


def detect_prompt_injection(text: str) -> bool:
    body = text or ""
    return any(pattern.search(body) for pattern in PROMPT_INJECTION_PATTERNS)


def sanitize_external_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for line in (text or "").splitlines():
        if any(pattern.search(line) for pattern in PROMPT_INJECTION_PATTERNS):
            continue
        cleaned_lines.append(line.strip())
    normalized = " ".join(part for part in cleaned_lines if part).strip()
    return normalized


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
