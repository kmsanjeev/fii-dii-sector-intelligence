"""
LLM Client with automatic provider fallback — engines/common/llm_client.py

Priority order (fastest/most-generous free tier first):
  1. Groq          (llama-3.1-8b-instant,  14,400 req/day)
  2. Cerebras      (llama3.1-8b,           ~100K tok/min)
  3. Gemini        (gemini-2.0-flash-lite,  1,500 req/day)
  4. OpenRouter    (llama-3.1-8b free,      no daily cap on free models)
  5. Together      (llama-3.1-8b-turbo,     $5 free credits)

All providers use the OpenAI-compatible chat completions API.
On rate-limit (429) or credit error (400/402), automatically rotates to next provider.

Usage:
    from engines.common.llm_client import call_llm

    response = call_llm(
        system="You are a financial analyst...",
        user="Headline: ...",
        max_tokens=300,
    )
    # response is a string (model output), or "" on total failure

.env keys required (add whichever you have — at least one needed):
    GROQ_API_KEY=gsk_...
    CEREBRAS_API_KEY=csk-...
    GEMINI_API_KEY=AIza...
    OPENROUTER_API_KEY=sk-or-...
    TOGETHER_API_KEY=...
"""

import os
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg   # triggers load_dotenv
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Provider definitions ──────────────────────────────────────────────────────
# Each entry: (env_var, base_url, model, extra_headers)
# base_url=None means use the provider's native SDK

_PROVIDERS = [
    {
        "name":         "Groq",
        "env_var":      "GROQ_API_KEY",
        "base_url":     "https://api.groq.com/openai/v1",
        "model":        "llama-3.1-8b-instant",   # confirmed working
        "extra_headers": {},
    },
    {
        "name":         "Cerebras",
        "env_var":      "CEREBRAS_API_KEY",
        "base_url":     "https://api.cerebras.ai/v1",
        "model":        "gemma-4-31b",             # confirmed working (llama models not on free tier)
        "extra_headers": {},
    },
    {
        "name":         "Gemini",
        "env_var":      "GEMINI_API_KEY",
        "base_url":     "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model":        "gemini-2.0-flash",        # valid model; 429 = daily quota reset at midnight
        "extra_headers": {},
    },
    {
        "name":         "Mistral",
        "env_var":      "MISTRAL_API_KEY",
        "base_url":     "https://api.mistral.ai/v1",
        "model":        "mistral-small-latest",   # free tier: 1B tokens/month, 1 req/s
        "extra_headers": {},
    },
    {
        "name":         "GitHubModels",
        "env_var":      "GITHUB_MODELS_TOKEN",
        "base_url":     "https://models.github.ai/inference",   # legacy azure URL 401s
        "model":        "openai/gpt-4o-mini",     # free with GitHub PAT (models:read)
        "extra_headers": {},
    },
    {
        "name":         "SambaNova",
        "env_var":      "SAMBANOVA_API_KEY",
        "base_url":     "https://api.sambanova.ai/v1",
        "model":        "Meta-Llama-3.3-70B-Instruct",  # free tier, fast
        "extra_headers": {},
    },
    {
        "name":         "OpenRouter",
        "env_var":      "OPENROUTER_API_KEY",
        "base_url":     "https://openrouter.ai/api/v1",
        "model":        "meta-llama/llama-3.3-70b-instruct:free",  # most reliable free model
        "extra_headers": {"HTTP-Referer": "https://github.com/kmsanjeev/fii-dii-sector-intelligence"},
    },
    {
        "name":         "Together",
        "env_var":      "TOGETHER_API_KEY",
        "base_url":     "https://api.together.xyz/v1",
        "model":        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "extra_headers": {},
    },
    {
        "name":         "OpenAI",
        "env_var":      "OPENAI_API_KEY",
        "base_url":     "https://api.openai.com/v1",
        "model":        "gpt-4o-mini",
        "extra_headers": {},
    },
]

# Track which providers are temporarily exhausted (reset after COOLDOWN_S)
_PROVIDER_COOLDOWN: dict[str, float] = {}
COOLDOWN_S = 300   # 5 minutes before retrying a rate-limited provider
MODEL_FAILURE_COOLDOWN_S = 3600  # invalid/retired model: do not retry this run


def _get_active_providers() -> list[dict]:
    now = time.time()
    active = []
    for p in _PROVIDERS:
        if not os.getenv(p["env_var"]):
            continue   # key not configured
        cd = _PROVIDER_COOLDOWN.get(p["name"], 0)
        if now < cd:
            logger.debug(f"[LLMClient] {p['name']} in cooldown for {int(cd - now)}s more")
            continue
        active.append(p)
    return active


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "quota" in msg or "too many" in msg


def _is_credit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "credit" in msg or "402" in msg or "billing" in msg
        or "insufficient" in msg or "balance" in msg
    )


def _is_model_unavailable_error(exc: Exception) -> bool:
    """Return True for a provider/model configuration failure.

    A retired or inaccessible model is deterministic, not transient.  It must
    be quarantined after the first failure instead of being retried for every
    management-sentiment symbol.
    """
    msg = str(exc).lower()
    return (
        "model_not_found" in msg
        or "model does not exist" in msg
        or "unknown model" in msg
        or "invalid model" in msg
        or ("404" in msg and "model" in msg)
    )


def call_llm(
    system: str,
    user: str,
    max_tokens: int = 300,
    temperature: float = 0.1,
) -> str:
    """
    Call the first available LLM provider. Auto-rotates on rate-limit or credit error.
    Returns the model's text response, or "" if all providers fail.
    """
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("[LLMClient] openai package not installed — run: py -3.11 -m pip install openai")
        return ""

    providers = _get_active_providers()
    if not providers:
        logger.error("[LLMClient] No LLM providers configured. Add at least one API key to .env")
        return ""

    for p in providers:
        api_key = os.getenv(p["env_var"], "")
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=p["base_url"],
                default_headers=p.get("extra_headers", {}),
                timeout=15.0,   # hard cap per-call; prevents 30s+ Groq hangs
            )
            resp = client.chat.completions.create(
                model=p["model"],
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            text = resp.choices[0].message.content or ""
            logger.debug(f"[LLMClient] {p['name']} OK ({len(text)} chars)")
            return text

        except Exception as exc:
            if _is_model_unavailable_error(exc):
                logger.error(
                    "[LLMClient] %s model unavailable; cooling down provider for %ss: %s",
                    p["name"], MODEL_FAILURE_COOLDOWN_S, exc,
                )
                _PROVIDER_COOLDOWN[p["name"]] = time.time() + MODEL_FAILURE_COOLDOWN_S
            elif _is_rate_limit_error(exc):
                logger.warning(f"[LLMClient] {p['name']} rate-limited — cooling down {COOLDOWN_S}s")
                _PROVIDER_COOLDOWN[p["name"]] = time.time() + COOLDOWN_S
            elif _is_credit_error(exc):
                logger.warning(f"[LLMClient] {p['name']} credit exhausted — cooling down {COOLDOWN_S}s")
                _PROVIDER_COOLDOWN[p["name"]] = time.time() + COOLDOWN_S
            else:
                logger.warning(f"[LLMClient] {p['name']} failed: {exc}")
            # Try next provider
            continue

    logger.error("[LLMClient] All providers failed or exhausted")
    return ""


def available_providers() -> list[str]:
    """Return names of configured (key present) providers."""
    return [p["name"] for p in _PROVIDERS if os.getenv(p["env_var"])]


if __name__ == "__main__":
    print("Configured providers:", available_providers())
    if not available_providers():
        print("No API keys found in .env")
    else:
        print("Testing LLM call...")
        result = call_llm(
            system="You are a financial analyst for Indian markets.",
            user='Headline: HDFC Bank Q4 profit rises 18%. Respond with JSON: {"sentiment": "BULLISH"}',
            max_tokens=50,
        )
        print("Response:", result)
