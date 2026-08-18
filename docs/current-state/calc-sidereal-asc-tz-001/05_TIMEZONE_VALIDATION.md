# Historical Timezone Validation

The fixed timezone corpus contains 64 cases over 12 IANA zones and years 1880–1990, plus explicit DST gap/fold, half-hour and quarter-hour cases. The runtime environment records Python 3.11.9 and the installed `tzdata` package version `2025.2`.

Statuses are separated as follows:

- `RESOLVED_IANA_HISTORICAL`: one valid IANA round-trip candidate with ordinary-second offset.
- `PRE_STANDARD_LMT`: a valid pre-standard local-mean-time offset requiring historical caution.
- `NONEXISTENT_LOCAL_TIME`: DST gap; no UTC instant is assigned.
- `AMBIGUOUS_UNRESOLVED`: DST fold; competing instants are retained without arbitrary choice.

No current-offset fallback is used. The policy is explicit source offset > validated IANA historical zone > source-provided offset > unresolved. Mutable city coordinates and timezone caches are not inputs to this corpus.
