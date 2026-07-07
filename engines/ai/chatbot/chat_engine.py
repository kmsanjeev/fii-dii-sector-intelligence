"""
Chat Engine -- Phase 14C (multi-provider with automatic fallback)
Orchestrates LLM API calls with function calling and RAG context injection.

Provider priority (all OpenAI-compatible):
  1. Groq         llama-3.3-70b-versatile    (best function calling, fastest)
  2. Gemini        gemini-2.0-flash            (good function calling support)
  3. OpenRouter    llama-3.3-70b-instruct:free (reliable free tier)
  4. Cerebras      llama-3.3-70b               (fast inference, if available)

On rate-limit (429 / "daily token limit") the engine automatically rotates to
the next configured provider for that turn. Each provider gets a 5-minute
cooldown before being retried.

Security:
  API keys are ALWAYS read from os.getenv() -- NEVER hardcoded.
"""

from __future__ import annotations
import json
import os
import time

from engines.common.logger import get_logger
from engines.ai.chatbot.intent_router import detect_intent, get_system_prompt
from engines.ai.chatbot.tools.tool_registry import TOOLS, TOOL_FUNCTIONS

logger = get_logger(__name__)

MAX_TOKENS      = 8192   # increased: detailed reports need headroom
MAX_TOOL_ROUNDS = 4
COOLDOWN_S      = 300   # 5 min before retrying a rate-limited provider

# ── Provider definitions (OpenAI-compatible) ──────────────────────────────────
_CHAT_PROVIDERS = [
    {
        "name":    "Groq",
        "env_var": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model":   "llama-3.3-70b-versatile",
        "extra_headers": {},
    },
    {
        "name":    "Gemini",
        "env_var": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model":   "gemini-2.0-flash",
        "extra_headers": {},
    },
    {
        "name":    "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "model":   "meta-llama/llama-3.3-70b-instruct:free",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/kmsanjeev/fii-dii-sector-intelligence"
        },
    },
    {
        "name":    "Cerebras",
        "env_var": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1",
        "model":   "llama-3.3-70b",
        "extra_headers": {},
    },
]


def _to_openai_tools(anthropic_tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool schema format to OpenAI function calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("input_schema", {"type": "object", "properties": {}, "required": []}),
            },
        }
        for t in anthropic_tools
    ]


OPENAI_TOOLS = _to_openai_tools(TOOLS)


def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "429" in msg or "rate_limit" in msg or "rate limit" in msg
        or "quota" in msg or "too many" in msg or "daily token" in msg
        or "tokens per day" in msg
    )


class ChatEngine:
    """
    Single-session chat engine with automatic provider fallback.
    Each instance maintains OpenAI-format message history for one session.
    """

    def __init__(self):
        try:
            from openai import OpenAI as _OpenAI
            self._OpenAI = _OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: py -3.11 -m pip install openai")

        self._cooldowns: dict[str, float] = {}
        self.history: list[dict] = []
        self._retriever = None

        # Ensure at least one provider is configured
        if not self._active_providers():
            raise EnvironmentError(
                "No chat provider API key found. Set at least one of: "
                "GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, CEREBRAS_API_KEY in .env"
            )

    def _active_providers(self) -> list[dict]:
        now = time.time()
        return [
            p for p in _CHAT_PROVIDERS
            if os.getenv(p["env_var"]) and now >= self._cooldowns.get(p["name"], 0)
        ]

    def _mark_rate_limited(self, name: str) -> None:
        self._cooldowns[name] = time.time() + COOLDOWN_S
        logger.warning("[ChatEngine] %s rate-limited — cooling down %ds", name, COOLDOWN_S)

    def _get_client(self, provider: dict):
        return self._OpenAI(
            api_key=os.getenv(provider["env_var"], ""),
            base_url=provider["base_url"],
            default_headers=provider.get("extra_headers", {}),
            timeout=60.0,
        )

    def chat(self, user_message: str) -> str:
        """
        Process one user turn and return the assistant's reply.
        Automatically rotates to the next provider if rate-limited.
        """
        intent       = detect_intent(user_message)
        system_prompt = get_system_prompt(intent)

        rag_context = self._get_rag_context(user_message, intent)
        if rag_context:
            system_prompt += f"\n\nRelevant intelligence context:\n{rag_context}"

        self.history.append({"role": "user", "content": user_message})

        providers = self._active_providers()
        if not providers:
            reply = (
                "All AI providers are temporarily rate-limited. "
                "Please try again in a few minutes."
            )
            self.history.append({"role": "assistant", "content": reply})
            return reply

        for provider in providers:
            client = self._get_client(provider)
            model  = provider["model"]
            logger.debug("[ChatEngine] Using provider: %s (%s)", provider["name"], model)

            result = self._run_turn(client, model, system_prompt, user_message)

            if result["status"] == "ok":
                reply = result["reply"]
                self.history.append({"role": "assistant", "content": reply})
                return reply.strip()

            if result["status"] == "rate_limited":
                self._mark_rate_limited(provider["name"])
                continue   # try next provider

            # Other error — log and try next provider
            logger.error("[ChatEngine] %s failed: %s", provider["name"], result.get("error"))
            continue

        # All providers exhausted
        reply = (
            "All AI providers are currently unavailable or rate-limited. "
            "Please try again in a few minutes."
        )
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def _run_turn(self, client, model: str, system_prompt: str, user_message: str) -> dict:
        """
        Run the full tool loop for one turn using the given client.
        Returns {"status": "ok", "reply": ...} or {"status": "rate_limited"} or {"status": "error", "error": ...}.
        """
        messages = [{"role": "system", "content": system_prompt}] + self.history

        tool_use_failed = False
        for _ in range(MAX_TOOL_ROUNDS):
            try:
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    tools=OPENAI_TOOLS,
                    tool_choice="auto",
                    parallel_tool_calls=False,
                )
            except Exception as e:
                if _is_rate_limit(e):
                    return {"status": "rate_limited"}
                err = str(e)
                if "tool_use_failed" in err:
                    logger.warning("[ChatEngine] tool_use_failed — forcing text response")
                    tool_use_failed = True
                    break
                return {"status": "error", "error": err}

            msg = response.choices[0].message

            if not msg.tool_calls:
                return {"status": "ok", "reply": msg.content or ""}

            # Append assistant tool-call turn
            messages.append({
                "role":       "assistant",
                "content":    msg.content,
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            # Execute tools and append results
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result = self._call_tool(tc.function.name, args)

                # Direct bypass for kundli: return formatted_report WITHOUT sending to LLM.
                # This avoids MAX_TOKENS truncation of the comprehensive multi-section report.
                if tc.function.name == "generate_personal_kundli":
                    report = result.get("formatted_report", "")
                    if report:
                        return {"status": "ok", "reply": report}
                    elif result.get("error"):
                        return {"status": "ok", "reply": f"Kundli computation failed: {result['error']}"}

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      json.dumps(result, default=str),
                })

        # Tool loop done (exhausted or tool_use_failed) — force final text call
        logger.warning(
            "[ChatEngine] %s — forcing final text response",
            "tool_use_failed" if tool_use_failed else "MAX_TOOL_ROUNDS exhausted",
        )
        tool_results = [m["content"] for m in messages if m.get("role") == "tool"]
        if tool_results:
            data_block    = "\n".join(tool_results[:6])
            final_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": (
                    f"Using this live market data:\n{data_block}\n\n"
                    f"Answer the question: {user_message}"
                )},
            ]
        else:
            final_messages = [{"role": "system", "content": system_prompt}] + self.history

        try:
            final = client.chat.completions.create(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=final_messages,
            )
            return {"status": "ok", "reply": final.choices[0].message.content or ""}
        except Exception as e:
            if _is_rate_limit(e):
                return {"status": "rate_limited"}
            return {"status": "error", "error": str(e)}

    def _call_tool(self, tool_name: str, tool_input: dict):
        fn = TOOL_FUNCTIONS.get(tool_name)
        if fn is None:
            logger.error("[ChatEngine] Unknown tool: %s", tool_name)
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            logger.debug("[ChatEngine] Calling tool: %s(%s)", tool_name, tool_input)
            return fn(**tool_input)
        except Exception as e:
            logger.error("[ChatEngine] Tool %s failed: %s", tool_name, e)
            return {"error": str(e)}

    def _get_rag_context(self, query: str, intent) -> str:
        if self._retriever is None:
            try:
                from engines.ai.knowledge.retriever import HybridRetriever
                self._retriever = HybridRetriever(top_k=5)
            except Exception as e:
                logger.warning("[ChatEngine] Retriever not available: %s", e)
                return ""
        try:
            results = self._retriever.retrieve(query, domain=None)[:3]
            return "\n".join(f"- {r['text'][:300]}" for r in results) if results else ""
        except Exception as e:
            logger.debug("[ChatEngine] RAG retrieval skipped: %s", e)
            return ""

    def reset(self):
        self.history = []
