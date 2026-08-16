# VEDA-EMP-POSEND-ACQ-001 - Existing State Audit

EMP-FEATURE-003 froze the `POSITION_END` feature family with hash
`da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297`.

This acquisition activity verifies that hash, reads the unchanged POP-001
timed-birth population, excludes all previously exposed subjects, and does not
import or calculate any feature logic during acquisition.

The source expansion uses birth-first selection from the 1,000-record timed
population. An event-first audit retains the prior seven legacy end events but
does not add them to the primary cohort.
