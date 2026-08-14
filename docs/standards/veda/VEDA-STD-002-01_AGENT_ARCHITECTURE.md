# Agent Architecture

The logical roles are Orchestrator, Research, Ingestion, Validation, Jyotisha Reasoning, Intuition/Pattern, Prediction, Outcome/Backtesting, and Response. They are workflow roles, not isolated autonomous services.

`engines.ai.orchestration` routes the smallest sufficient workflow and uses the existing unified retriever and research platform. Existing chat routing, document learning, domain synthesis, and phase prediction engines remain reusable components.
