# Prediction Registry

`DurablePredictionRegistry` persists prediction payloads in the existing research-platform SQLite database. Creation is idempotent, records lock by default, and preserves method, rule, knowledge, workflow, confidence, event, window, chart, and evidence metadata. Supersession creates a new identity and marks the old record `SUPERSEDED`.
