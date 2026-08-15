# P027 Architecture

`P027SynthesisEngine` consumes evidence emitted by existing engines:

`facts -> existing rules -> SynthesisEvidence -> lineage clusters -> roles -> convergence/contradiction -> timing -> confidence -> trace`

The implementation is deterministic and provider-free. `PRODUCTION_SAFE` excludes experimental/research-archive evidence and ML signals. Research and shadow callers may pass labeled evidence explicitly. The output is a synthesis artifact; existing ChatEngine remains responsible for presentation.

Precedence is explainable: knowledge-zone authority, then declared strength, then validation state. This is not a majority vote and confidence is not a raw evidence count.
