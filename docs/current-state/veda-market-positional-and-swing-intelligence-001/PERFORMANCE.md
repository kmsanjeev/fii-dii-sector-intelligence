# Performance evidence

Local deterministic probes after the F&O projection reuse measured roughly:

- PAYTM detail: SWING about 2.1s; POSITIONAL about 0.6s.
- Theme-enabled detail: representative symbols about 0.4–2.6s.
- SWING screen limit 3: about 6.8s with 2,143 technical-universe rows,
  1,692 prefiltered rows and 20 deep-analyzed candidates.

These are local probes, not a production SLO. Provider calls added: 0.
