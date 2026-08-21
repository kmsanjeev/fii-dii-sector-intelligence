# Evidence coverage

Coverage is field-level: expected fields, observed fields, usable fields and a
bounded quality state are emitted. A populated row is not treated as complete
evidence. The quality state is `HIGH`, `MEDIUM`, `LIMITED` or `INSUFFICIENT`.

Coverage is not predictive accuracy, investment conviction, or a replacement
for source validation. Legacy and semantically unsafe fields do not count as
usable merely because they contain a number.
