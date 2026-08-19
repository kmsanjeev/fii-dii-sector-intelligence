# Birth-time uncertainty

Tara Bala needs Janma Nakshatra; Chandra Bala needs natal Moon sign. DOB/TOB/POB
are dependencies only when VEDA derives those facts. If an uncertainty interval
keeps the Moon in one Nakshatra or sign, the corresponding fact can be marked
`JANMA_NAKSHATRA_STABLE` or its Moon-sign equivalent. If the interval crosses a
boundary, the personal factor must be `JANMA_NAKSHATRA_UNCERTAIN` or
`BIRTH_DATA_INSUFFICIENT` and abstain/downgrade.

This is a design contract, not rectification. It does not infer a birth time or
silently substitute a neutral value. General Muhurta remains usable.
