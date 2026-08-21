# Theme Model

Theme is a many-to-many structural classification layer between Sector and
Stock. A symbol may have zero, one or multiple active Theme memberships. Theme
membership is not a price score and does not imply leadership.

The machine contract is `theme-intelligence-1.0` and the stable registry is
`data/reference/veda_theme_registry.json`. The initial registry contains 15
bounded codes with stable IDs, aliases and descriptions. The service has no
theme-specific `if theme == ...` calculation branches.

Membership fields include symbol, optional ISIN, theme ID/code,
relationship/exposure, evidence, method, confidence, quality, effective and
verification dates, source, limitations and status.
