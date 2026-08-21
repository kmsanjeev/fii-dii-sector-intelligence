# Options Chain Contract

The provider seam preserves underlying identity, expiry, strike, CE/PE, LTP,
OI, previous OI where supplied, volume, IV, bid/ask and provider-supplied
Greeks. Provider Greeks are labelled source-provided; VEDA does not calculate
Greeks. Ordinary option OI is not FII/DII positioning. The official Dhan
option-chain limit is recorded as one unique request per three seconds and no
continuous all-underlying polling is enabled.
