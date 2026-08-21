# Date alignment and freshness

F&O output is EOD and source-conditioned. The audited latest local source is 2026-08-19. `data_status` exposes state, as-of date, source, last successful update and limitations. Current futures basis is calculated only when the source row contains an underlying price on the same trade date; otherwise it remains null. Cross-layer exposes the F&O date separately from participant and cash dates.

NSE's current F&O feed specification states that the Bhavcopy is generated at
around 17:00 IST and contains end-of-day contract values. This supports the
EOD classification but does not guarantee that every trading day has already
been acquired locally.
