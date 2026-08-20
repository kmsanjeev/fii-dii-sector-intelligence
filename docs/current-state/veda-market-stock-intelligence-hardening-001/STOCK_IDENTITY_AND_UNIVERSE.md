# Stock identity and universe

The request symbol is upper-cased and matched exactly. The equity master is the identity authority; aliases and fuzzy matching are not silently applied. Existing bull-run rows remain a legacy enrichment source, but their absence no longer makes an identified equity appear unknown when price/technical sources are available.

Identity states are `IDENTIFIED`, `UNKNOWN_SYMBOL`, `IDENTITY_SOURCE_UNAVAILABLE`, and `NOT_SUPPORTED`. The contract reports company, ISIN, series, listing date, active state, sector and the identity source where available.
