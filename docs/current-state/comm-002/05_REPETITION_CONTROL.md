# Repetition Control

Recent assistant history is inspected for repeated opening and closing phrases. When repeated phrases are detected, the profile switches to `STRICT` repetition avoidance and guidance asks ChatEngine to vary entry and close rather than applying random synonym rotation. The control also suppresses repeated offer-to-continue boilerplate and repeated long safety language while preserving required safety meaning.

Human response repetition quality remains a separate validation question; this phase validates deterministic detection and guidance, not fabricated human preference.
