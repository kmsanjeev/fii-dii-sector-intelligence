"""
Chat Engine -- Phase 14C (Groq backend)
Orchestrates Groq API calls with function calling and RAG context injection.

Flow:
  1. Detect intent (intent_router)
  2. Retrieve RAG context (engines/ai/knowledge/retriever)
  3. Build system prompt (domain-specific from intent_router)
  4. Call Groq llama-3.3-70b-versatile with tools + RAG context
  5. Handle tool_calls (call data_tools functions)
  6. Return final assistant text

Security:
  GROQ_API_KEY is ALWAYS read from os.getenv() -- NEVER hardcoded.
  If not set, ChatEngine raises EnvironmentError at init time.
"""

from __future__ import annotations
import json
import os

from engines.common.logger import get_logger
from engines.ai.chatbot.intent_router import detect_intent, get_system_prompt
from engines.ai.chatbot.tools.tool_registry import TOOLS, TOOL_FUNCTIONS

logger = get_logger(__name__)

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 3  # keep token budget low on Groq free tier (100k/day)


def _to_groq_tools(anthropic_tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool schema format to OpenAI/Groq function calling format."""
    groq_tools = []
    for t in anthropic_tools:
        groq_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("input_schema", {"type": "object", "properties": {}, "required": []}),
            },
        })
    return groq_tools


GROQ_TOOLS = _to_groq_tools(TOOLS)


class ChatEngine:
    """
    Single-session chat engine backed by Groq (Llama 3.3 70B).
    Each instance maintains OpenAI-format message history for one session.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable not set. "
                "Get a free key at console.groq.com and add it to .env"
            )
        try:
            from groq import Groq
            self.client = Groq(api_key=api_key)
        except ImportError:
            raise ImportError("groq package not installed. Run: py -3.11 -m pip install groq")

        self.history: list[dict] = []
        self._retriever = None

    def _get_retriever(self):
        if self._retriever is None:
            try:
                from engines.ai.knowledge.retriever import HybridRetriever
                self._retriever = HybridRetriever(top_k=5)
            except Exception as e:
                logger.warning(f"[ChatEngine] Retriever not available: {e}")
        return self._retriever

    def chat(self, user_message: str) -> str:
        """
        Process one user turn and return the assistant's reply.
        Maintains conversation history across calls.
        """
        intent = detect_intent(user_message)
        system_prompt = get_system_prompt(intent)

        # Inject RAG context into system prompt
        rag_context = self._get_rag_context(user_message, intent)
        if rag_context:
            system_prompt += f"\n\nRelevant intelligence context:\n{rag_context}"

        self.history.append({"role": "user", "content": user_message})

        # Build full message list: system + history
        messages = [{"role": "system", "content": system_prompt}] + self.history

        # Agentic tool loop — model gathers data via tools before answering
        tool_use_failed = False
        for _ in range(MAX_TOOL_ROUNDS):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    tools=GROQ_TOOLS,
                    tool_choice="auto",
                    parallel_tool_calls=False,  # prevents Llama 3.3 XML-style malformed calls
                )
            except Exception as e:
                err_str = str(e)
                if "tool_use_failed" in err_str:
                    # Llama 3.3 generated XML-style function call — break to final text call
                    logger.warning("[ChatEngine] tool_use_failed from Groq — forcing text response")
                    tool_use_failed = True
                    break
                if "rate_limit_exceeded" in err_str or "429" in err_str:
                    # Groq daily token limit hit — surface it to the user immediately
                    reply = (
                        "The AI API daily token limit has been reached. "
                        "Please wait a few minutes and try again, or upgrade at console.groq.com."
                    )
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
                raise

            msg = response.choices[0].message

            if not msg.tool_calls:
                # Model produced a final text response — we're done
                reply = msg.content or ""
                self.history.append({"role": "assistant", "content": reply})
                return reply.strip()

            # Append assistant message with tool_calls
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            # Execute each tool and append results
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result = self._call_tool(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

        # Tool loop exhausted or tool_use_failed — force one final text-only call.
        # Build a clean prompt from the tool results gathered so far rather than
        # passing the full messy tool-call history, which confuses the model.
        logger.warning(
            "[ChatEngine] %s — forcing final text response",
            "tool_use_failed" if tool_use_failed else "MAX_TOOL_ROUNDS exhausted",
        )
        tool_results = [m["content"] for m in messages if m.get("role") == "tool"]
        if tool_results:
            data_block = "\n".join(tool_results[:6])
            final_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (
                    f"Using this live market data:\n{data_block}\n\n"
                    f"Answer the question: {user_message}"
                )},
            ]
        else:
            final_messages = [{"role": "system", "content": system_prompt}] + self.history

        try:
            final = self.client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=final_messages,
            )
            reply = final.choices[0].message.content or ""
        except Exception as e:
            err_str = str(e)
            if "rate_limit_exceeded" in err_str or "429" in err_str:
                reply = (
                    "The AI API daily token limit has been reached. "
                    "Please wait a few minutes and try again, or upgrade at console.groq.com."
                )
            else:
                logger.error(f"[ChatEngine] Final text call failed: {e}")
                reply = ""

        self.history.append({"role": "assistant", "content": reply})
        return reply.strip() or "I was unable to complete this request. Please try again."

    def _call_tool(self, tool_name: str, tool_input: dict):
        """Execute a registered tool and return its result."""
        fn = TOOL_FUNCTIONS.get(tool_name)
        if fn is None:
            logger.error(f"[ChatEngine] Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            logger.debug(f"[ChatEngine] Calling tool: {tool_name}({tool_input})")
            return fn(**tool_input)
        except Exception as e:
            logger.error(f"[ChatEngine] Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    def _get_rag_context(self, query: str, intent) -> str:
        """Fetch RAG context for the query (max 3 docs)."""
        retriever = self._get_retriever()
        if retriever is None:
            return ""
        try:
            results = retriever.retrieve(query, domain=None)[:3]
            if not results:
                return ""
            return "\n".join(f"- {r['text'][:300]}" for r in results)
        except Exception as e:
            logger.debug(f"[ChatEngine] RAG retrieval skipped: {e}")
            return ""

    def reset(self):
        """Clear conversation history."""
        self.history = []
