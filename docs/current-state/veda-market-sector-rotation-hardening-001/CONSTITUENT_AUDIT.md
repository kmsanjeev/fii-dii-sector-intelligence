# Constituent audit

Current breadth uses the current `company_classification_v4` universe and is
explicitly labelled `CURRENT_CONSTITUENT_UNIVERSE`. It is not a historical
membership reconstruction. A stock may be absent from a particular bhavcopy,
renamed, suspended or otherwise unusable; that absence reduces `usable` and
`coverage_pct`.

The current engine exposes, for 1D/5D/20D windows:

- expected constituent count;
- usable constituent count;
- coverage percentage;
- positive constituent percentage.

Top and lagging names are reported as top-performing constituents, not exact
index contributions, because official index weights are not used. No
survivorship-free historical breadth claim is made.
