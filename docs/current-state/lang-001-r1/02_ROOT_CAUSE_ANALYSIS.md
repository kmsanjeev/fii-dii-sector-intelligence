# Root-Cause Analysis

The resolver previously selected duplicate canonical records by insertion
order, allowing Hinglish professional records to mask English internet slang
and abbreviation semantics. It only recognised two literal contexts, had no
controlled Hindi inflection aliases, used English-first metalinguistic markers,
and did not prefer the longest contextual match.

The benchmark scorer also treated a correct no-match `NONE` result as a
failure. Nine fixture metadata defects were corrected and retained in the
baseline record; expected labels were not changed to inflate resolver output.
