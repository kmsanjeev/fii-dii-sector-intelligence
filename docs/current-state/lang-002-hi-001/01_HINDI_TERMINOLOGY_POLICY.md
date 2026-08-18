# Hindi Terminology Policy

Hindi is a presentation locale, not a second Jyotisha ontology. Canonical
IDs remain English-like machine identifiers such as
`TERM.PLANET.JUPITER`; the Hindi display is `गुरु`. Devanagari technical and
Sanskrit forms are retained where they are the established technical label:
`नवांश`, `विंशांश`, `विंशोत्तरी दशा`, `तिथि`, `नक्षत्र`, `योग`, and `करण`.

The pack covers all 33 existing terms: nine planets, twelve Rashis, one
Nakshatra, four Vargas, two Dasha terms, and five Panchanga terms. Hindi
aliases are presentation lookup only and can resolve to an existing canonical
ID when the `hi` locale is supplied. No calculation parser or business-logic
identifier was changed.

All Hindi entries are `MACHINE_DRAFT` / `REVIEW_PENDING`. The terminology
reference is the existing governed registry and its inherited ontology source
paths, plus the Hindi language boundary in STD-003. This is not a claim of
human linguistic or source review.
