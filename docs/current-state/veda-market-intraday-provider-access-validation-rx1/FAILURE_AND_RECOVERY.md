# Failure and recovery

The token lifecycle self-heals after a missed scheduler window by checking the
secure cached token and generating a fresh TOTP token when near expiry. The
documented Dhan token-generation throttle is respected by token reuse.

Known current failure is entitlement, not authentication. The resolver returns
no selected intraday provider while retaining local EOD operation. There is no
silent live-to-EOD fallback and no empty overwrite of local data.

The Dhan SDK constructor defect and provider failure-envelope parsing defect
found during this activity were repaired and covered by focused tests.
