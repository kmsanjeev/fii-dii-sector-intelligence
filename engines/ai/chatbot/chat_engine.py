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
MAX_TOOL_ROUNDS = 5  # prevent infinite tool loops


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

        # Agentic loop: model may call tools multiple times
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
                # Llama 3.3 occasionally generates XML-style function calls (not JSON).
                # Groq returns 400 'tool_use_failed' in that case — answer from RAG context instead.
                if "tool_use_failed" in str(e):
                    logger.warning("[ChatEngine] tool_use_failed from Groq — retrying without tools")
                    response = self.client.chat.completions.create(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        messages=messages,
                    )
                else:
                    raise

            msg = response.choices[0].message

            if msg.tool_calls:
                # Append assistant message with tool_calls to history
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
                continue

            # No tool calls — final text response
            reply = msg.content or ""
            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        return "I was unable to complete this request. Please try again."

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
