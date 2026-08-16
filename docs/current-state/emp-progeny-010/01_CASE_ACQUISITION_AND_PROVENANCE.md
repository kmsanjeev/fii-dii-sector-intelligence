# Case Acquisition and Provenance

Implementation: `scripts/veda_emp_progeny_010.py`

The ledger runs a birth-first lane using public OGDB timed records and public
family/event evidence. Selection fields are birth quality, identity, event
precision, event provenance and timezone usability. Chart fit is explicitly
false for every case. The persisted artifact is
`data/veda/research/empirical/veda_emp_progeny_010_pilot.json`.

Accepted cases:

| Case | Subject | Event | Precision | Sequence | Evidence quality |
|---|---|---|---|---|---|
| 001 | Brigitte Bardot | Nicolas-Jacques Charrier, 1960-01-11 | Exact day | First | Strong referenced |
| 002 | Candice Bergen | Chloe Malle, 1985-11-08 | Exact day | First | Strong referenced |
| 003 | Diana Ross | Rhonda Ross Kendrick, 1971-08 | Month | First | Strong referenced |
| 004 | Robert Redford | Scott Anthony, 1959-09-01 | Exact day | First | Strong referenced |
| 005 | Irène Joliot-Curie | Hélène, 1927 | Year | First | Strong referenced |
| 006 | Charles Aznavour | Seda, 1947-05-21 | Exact day | First | Primary verified |
| 007 | Paul Newman | Scott Newman, 1950-09-23 | Exact day | First | Strong referenced |
| 008 | Vincent Auriol | Paul, 1919 | Year | First | Strong referenced |
| 009 | Howard Baker | Darek Baker, 1953 | Year | First | Primary verified |
| 010 | Walter Annenberg | Wallis, 1939 | Year | Sequence uncertain | Single referenced |

The ledger retains explicit exclusion examples rather than silently dropping
them: Jean-Paul Belmondo was excluded for conflicting public dates, Albert
Einstein for sequence ambiguity plus unresolved timezone, and Clint Eastwood
for ambiguous parenthood evidence. No private individuals or prospective
reproductive outcomes were used.
