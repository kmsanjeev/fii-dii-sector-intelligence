# VEDA-RM-002 Method Comparison — D20 Variant Pair

Status: `PASS_WITH_CONDITION`  
Activity: `METHOD_COMPARISON`  
Date: 2026-08-16

## Question

Which two legitimate D20 method variants produce the better-governed result
for the same calculation input?

## Compared methods

| Variant | Runtime identifier | Governance position |
|---|---|---|
| Historical generic fallback | `D20_LEGACY_GENERIC_VARGA_V0` / `general` | Retained for explicit historical comparison; not the governed D20 default |
| Source-selected D20 route | `D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1` / `d20_vimshamsha_bphs_category_start_v1` | Governed D20 default; `PARTIALLY_VALIDATED`, with `SOURCE_MAPPING_INCOMPLETE` and interpretation `NOT_VALIDATED` |

The source-selected route uses the BPHS category-start evidence already recorded
in P015-RX2. Its sequential destination-sign progression remains explicitly
evidence-qualified; this comparison does not promote that inference to a
fully source-resolved formula.

## Shared deterministic input

The same 240 longitude fixtures were passed to both methods: every one of the
12 source signs, with 20 equal D20 subdivisions sampled at each subdivision's
midpoint. These are calculation fixtures, not empirical cases, subjects,
outcomes, or predictive observations.

## Result

| Measure | Result |
|---|---:|
| Shared fixtures | 240 |
| Exact output agreement | 20 |
| Divergent outputs | 220 |
| Agreement rate | 8.33% |
| Divergence rate | 91.67% |

| Source-sign modality | Fixtures | Agreement | Divergence |
|---|---:|---:|---:|
| Movable | 80 | 20 | 60 |
| Fixed | 80 | 0 | 80 |
| Dual/common | 80 | 0 | 80 |

The generic fallback agrees only for the sampled Aries subdivision route. It
diverges across every sampled fixed and dual/common sign, and across the
non-Aries movable signs. This confirms that the two routes are materially
different methods rather than interchangeable labels.

## Decision

The source-selected D20 route is the better-governed default because it carries
explicit method identity, BPHS source references, category-start provenance and
an unresolved-mapping status. The legacy route remains useful as a named
historical baseline, but must not be silently mixed with governed D20 output.

This is a governance and calculation-routing decision only. It does not show
that either method predicts spiritual, life-domain or event outcomes better;
no interpretation was activated, no Approved Core promotion occurred, and all
human-validation statuses remain unchanged.

## Validation and limitations

- The comparison was reproduced directly through
  `engines.ai.knowledge.varga_governance.varga_sign`.
- Existing P015-RX2 boundary, grid, runtime and acceptance evidence remains the
  authority for the selected implementation.
- Midpoint fixtures do not resolve boundary sensitivity or the unresolved
  destination-sign/deity mapping.
- No empirical, prospective, calibration, ML or production-behaviour claim is
  made.

## Resumable next step

Keep `D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1` as the explicit governed route and
retain `D20_LEGACY_GENERIC_VARGA_V0` only for labelled historical comparison.
The next independent activity may examine the available Tajika foundation or
Ashtakavarga/Shadbala validation track; it must preserve the same separation
between deterministic calculation evidence and interpretation or prediction.
