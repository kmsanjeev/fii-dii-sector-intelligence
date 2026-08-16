# Research Export Review

The synthetic export review passes its design checks: direct identifiers,
identity-vault references, document contents, birth date/time fields and
uncontrolled free text are absent from the export shape. Export scope is
`DEIDENTIFIED_RESEARCH_SHARING`; the snapshot is frozen by hashes and export
activity must be logged.

Before real export, an analyst must review reidentification risk, small-cell
geography/date combinations, consent scope, linkage keys, free text, source
license and recipient controls. Pseudonymization is not anonymity.
