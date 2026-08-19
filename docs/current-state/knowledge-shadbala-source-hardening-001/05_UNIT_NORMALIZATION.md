# Unit Normalization

The inspected source expresses Shadbala component values in **Virupas**, with 60 Virupas equal to one Rupa. The current runtime returns values such as 60, 30 and 15 while labelling them `RUPA`; this is a source/runtime unit mismatch. The current Naisargika comment also claims a 420 total, while the source-witness value sequence sums to 240 Virupas (4 Rupas). This is recorded as a remediation finding, not corrected here.

The current `VIMSHOPAKA_WEIGHTS` table is not accepted as a Shadbala aggregation contract. The audited strength passage describes six Bala sources and Virupa thresholds; it does not establish that a 16-division Vimshopaka weight factor should normalize their sum. The current factor evaluates to 1 and therefore masks the issue rather than resolving it.
