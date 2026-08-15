# VEDA-AUTOLOOP-R3

Status: `IMPLEMENTED / FROZEN`

VEDA-AUTOLOOP-R3 replaces availability-only selection with a bounded
information-gain scheduler. Each activity has a concrete question and
expected evidence class. The controller computes a stable relevant-input
fingerprint, persists bounded activity history and output fingerprints, and
records a concise candidate-selection trace.

Unchanged inputs plus a prior `NO_NEW_INFORMATION`, `LOW_INFORMATION_GAIN`,
or `DOCUMENTATION_ONLY` result suppress the activity. Cooldowns are released
by changed inputs, new source/dependency/method state, a justified expiry, or
an explicit manual override. A new Markdown report is not material progress
unless it contains a new authoritative conclusion; a zero-commit validation
can still count when it closes a blocker, distinguishes a method, or records a
new evidence/validation finding.

Selection applies information gain, novelty, stable priority, and a
same-track diversity bias. `METHOD_COMPARISON` remains the next priority and
requires two legitimate methods, a specific question, shared inputs,
independent outputs, comparison criteria, and source authority. The controller
does not execute that research during R3.

Empirical and prospective input-preparation tracks retain their legitimate
input blockers. Generic validation and governance reconciliation are not
repeated merely because they remain configured. If all candidates are
blocked, cooled down, or exhausted, the controller records
`ROADMAP_REBASELINE_REQUIRED` before treating the state as an ordinary
`ALL_TRACKS_BLOCKED` stop.

R3 is controller hardening only. No Jyotisha rule, source claim, predictive
maturity, empirical case, provider call, or RAG store was changed.
