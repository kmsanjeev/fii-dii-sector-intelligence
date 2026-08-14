# Outcome Registry

Outcomes are separate durable records with event, period, direction, evidence source, verification quality, timestamp, and notes. Supported verification states are `UNVERIFIED`, `USER_REPORTED`, `DOCUMENT_VERIFIED`, `DATA_VERIFIED`, `SYSTEM_VERIFIED`, and `MULTI_SOURCE_VERIFIED`. Outcomes never rewrite prediction-time evidence.
