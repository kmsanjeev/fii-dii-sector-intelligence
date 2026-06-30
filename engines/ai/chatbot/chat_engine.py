"""
Chat Engine -- Phase 14C
Orchestrates Claude API calls with tool use and RAG context injection.

Flow:
  1. Detect intent (intent_router)
  2. Retrieve RAG context (engines/ai/knowledge/retriever)
  3. Build system prompt (domain-specific from intent_router)
  4. Call Claude claude-sonnet-4-6 with tools + RAG context
  5. Handle tool_use blocks (call data_tools functions)
  6. Return final assistant text

Security:
  ANTHROPIC_API_KEY is ALWAYS read from os.getenv() -- NEVER hardcoded.
  If not set, ChatEngine raises EnvironmentError at init time.
"""

from __future__ import annotations
import json
import os
from typing import Optional

from engines.common.logger import get_logger
from engines.ai.chatbot.intent_router import detect_intent, get_system_prompt
from engines.ai.chatbot.tools.tool_registry import TOOLS, TOOL_FUNCTIONS

logger = get_logger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 5  # prevent infinite tool loops


class ChatEngine:
    """
    Single-session chat engine that handles multi-turn conversations.
    Each ChatEngine instance maintains message history for one session.
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it before starting the chatbot."
            )
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: py -3.11 -m pip install anthropic")

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

        # Inject RAG context as first-turn system context
        rag_context = self._get_rag_context(user_message, intent)
        if rag_context:
            system_prompt += f"\n\nRelevant intelligence context:\n{rag_context}"

        self.history.append({"role": "user", "content": user_message})

        # Agentic loop: Claude may call tools multiple times
        for round_num in range(MAX_TOOL_ROUNDS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=TOOLS,
                messages=self.history,
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                text = _extract_text(response)
                self.history.append({"role": "assistant", "content": response.content})
                return text

            if response.stop_reason == "tool_use":
                # Process all tool calls in this response
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._call_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, default=str),
                        })

                # Add assistant response + tool results to history
                self.history.append({"role": "assistant", "content": response.content})
                self.history.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason
            logger.warning(f"[ChatEngine] Unexpected stop_reason: {response.stop_reason}")
            break

        return "I was unable to complete this request. Please try again."

    def _call_tool(self, tool_name: str, tool_input: dict):
        """Execute a tool and return the result."""
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
        """Fetch RAG context for the query (max 3 docs to stay within context budget)."""
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
        """Clear conversation history (start new session)."""
        self.history = []


def _extract_text(response) -> str:
    """Extract plain text from Claude API response content blocks."""
    parts = []
    for block in response.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts).strip()
