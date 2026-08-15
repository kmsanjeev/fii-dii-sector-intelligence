# VEDA-AUTOLOOP-R4

Status: `IMPLEMENTED / FROZEN`

R4 separates a bounded run stop from a programme stop. `LOW_VALUE_REPETITION`,
`MAX_LOOPS_REACHED`, and current-run cooldown exhaustion are transient run
stops. At startup the controller classifies a stopped state, validates the
stored next priority against current candidates, and resumes an eligible
priority without requiring human intervention. The historical stop is retained
in `stop_history`, while the active run clears the stale stop reason and keeps
the programme `ACTIVE`.

Human blocks and programme stops remain stopped. A cooldown remains scoped to
its activity and cannot freeze unrelated tracks. Dry-run reports the resume
classification and predicted transition without mutation. Maximum-loop
completion remains resumable. R4 does not add Tajika or other Jyotisha scope.
