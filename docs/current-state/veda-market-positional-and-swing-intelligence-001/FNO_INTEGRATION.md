# F&O integration

F&O is confirmatory context only. Non-applicable symbols return
`FNO_NOT_APPLICABLE`, not negative evidence. A detected roll transition returns
limited confirmation rather than being treated as a directional signal. The
implementation consumes the already-loaded governed `fno_intel` projection;
raw per-symbol rebuilding is only a guarded fallback. CSV boolean values are
parsed explicitly so textual `False` cannot become truthy.
