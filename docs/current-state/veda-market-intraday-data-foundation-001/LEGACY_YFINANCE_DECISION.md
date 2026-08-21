# Legacy yfinance Decision

The existing chart route still uses yfinance for 5M/15M/1H query-time bars.
It is non-persistent, has source/rate-limit/history limitations, and is not
governed trading evidence. Its timestamp/display behavior is isolated to the
chart compatibility path. Governed Intraday routes never silently fall back to
yfinance; they report source or identity failure explicitly.
