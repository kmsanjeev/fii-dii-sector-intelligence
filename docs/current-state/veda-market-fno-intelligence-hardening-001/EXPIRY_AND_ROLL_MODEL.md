# Expiry, selection and roll model

Nearest expiry is the earliest valid non-expired expiry per underlying. It is not the highest-OI contract. Liquidity tie-breaking within that expiry is volume, open interest, turnover, expiry and contract identifier.

Most-active is a separate diagnostic selection: volume, open interest, turnover, expiry and contract identifier. Both policies are named in the contract.

If the selected expiry changes between adjacent sessions, the record is `ROLL_TRANSITION`; cross-expiry price comparison is withheld. Five-session OI is emitted only when the current selected expiry is present in every bounded session. Otherwise it is null with continuity false.
