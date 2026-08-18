# Candidate Window Model

`build_candidate_windows(start, end, transition_points, interval_evidence)`
is a deterministic research primitive. It:

- requires timezone-aware boundaries;
- sorts explicit transition instants in UTC order;
- creates adjacent half-open segments;
- preserves transition metadata and optional evidence;
- emits `selection_status=INACTIVE`, `recommendation_status=NOT_AUTHORIZED`,
  and `score=null` for every segment.

It does not compute a best time, resolve conflicts, apply personal Bala, or
call a provider. Transition points must be supplied by a governed caller;
the foundation does not silently invent planetary or event transitions.
