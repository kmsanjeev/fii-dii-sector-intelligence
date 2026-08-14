# Runtime Integration

The actual `ChatEngine.chat()` path now calls the cheap Stage-A `AgentOrchestrator.shadow_trace()` after intent detection. It records intent, mode, capabilities, request ID, and prediction intent on `last_orchestration`; the backend chat response exposes this trace as `orchestration`. The existing retrieval, tool, provider, and response flow remains primary and unchanged.

Primary orchestration is not enabled. Assisted response integration remains future work after benchmark evidence.
