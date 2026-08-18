# Unicode Validation

The runtime reads and writes UTF-8 and serializes JSON with `ensure_ascii=False`.
Focused tests cover Devanagari, IAST diacritics, mixed English/Sanskrit text,
and JSON round-trip behavior. The test fixture is presentation-only; it does
not create a new Sanskrit source or language-specific truth.

Canonical IDs and API enums remain ASCII and stable. Unicode display text is
never parsed back into calculation inputs.
