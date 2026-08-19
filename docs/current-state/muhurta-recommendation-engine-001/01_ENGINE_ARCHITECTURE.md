# Engine Architecture and Blocker

The intended implementation boundary is a reusable internal service consuming
P032 Panchanga facts and immutable activity contracts. It would expose
categorical rule traces, precedence, abstention, caution, consultation and
deterministic results. It would not score, rank, predict, or use personal Bala.

That service is not activated in this activity. A contract conformance gate
was implemented instead. It accepts only explicit machine bindings such as an
evaluator/predicate identifier plus machine operands or factor values. It never
parses natural-language source conditions.

Both accepted business and education contracts fail that gate. Implementing
their Nakshatra or Tithi/Karana rules would require inventing mappings absent
from the frozen contracts. Under the programme rules, that is a contract
implementation blocker, not an implementation detail.
