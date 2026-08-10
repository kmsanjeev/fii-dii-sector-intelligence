# VEDA-P004 Graha, Node & Retrograde Validation

Validated core grahas:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn
- Rahu
- Ketu

Validation summary:

- Sampled longitudes matched independent direct `swisseph` references within tight tolerance.
- Rahu is calculated from `TRUE_NODE` in the active runtime path.
- Ketu is derived as `Rahu + 180°`, normalized to `0..360`.
- Retrograde state matched sampled speed-sign references for Mercury, Venus, Mars, Jupiter, Saturn, and the nodes.

Non-core active entities:

- REST/stock/country runtime also surfaces `Uranus` and `Neptune`.
