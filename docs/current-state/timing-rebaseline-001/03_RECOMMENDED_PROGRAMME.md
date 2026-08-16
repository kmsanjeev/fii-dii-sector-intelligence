# VEDA-TIMING-RESEARCH-REBASELINE-001 — Recommended Programme

Primary lane: `VEDA-EMP-FEATURE-001` — source-ranked feature-level empirical
analysis.

Objective: test individually frozen, source-attributed feature hypotheses
against objective event windows without claiming that empirical association is
classical doctrine.

Required feature matrix:

`case_id`, `event_id`, `event_family`, `feature_id`, `feature_source_status`,
`feature_value`, `event_window`, `control_window`, `method_version`,
`source_version`, `birth_quality`, `leakage_audit`.

Design requirements:

- use existing CaseRegistry, controls, holdout and PRED contracts;
- start with legitimate existing cases only; do not fabricate or automatically
  resume EMP-050;
- separate textual authority from empirical association;
- freeze event definitions and feature calculations before scoring;
- retain source tiers: classical, practitioner, platform and experimental;
- reserve a sealed holdout and report effect size/non-association;
- no ML model, composite score or production activation.

Success: at least one pre-registered feature survives leakage review, has
reliable event/control definitions and produces an interpretable association
or non-association estimate on held-out data.

Failure: no eligible cases, leakage, unstable feature definitions, or no
discrimination after the frozen test. Stop if the feature contract must be
changed after outcomes are visible.
