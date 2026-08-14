# Multi-Turn State

Recent user turns are consulted for transitions and short follow-up stability.
The result exposes `transition_from`, `transition_confidence`, and
`state_stable`. A short `Okay` can retain an established context instead of
resetting to small talk. Existing bounded ChatEngine history is reused; no
second conversation database was created.

Ten transition fixtures cover social-to-emotional, domain-to-candid,
emotional-to-motivational, and competitive paths.
