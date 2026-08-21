# Snapshot lifecycle

Two local ignored artifacts are now used:

- `data/NSE/nsecache/theme_intelligence/membership_snapshot.json`
- `data/NSE/nsecache/theme_intelligence/price_projection.json`

Membership snapshot inputs are the Theme registry, classification source,
Theme tagging source, and fundamentals identity source. Their content
fingerprint is stored with the artifact. The canonical artifact hash is
validated before use. Invalid, missing, or corrupt artifacts are rebuilt by
the bounded source builder.

The price projection is derived from the current membership universe and
bounded 1D/3D/5D/10D/20D returns. Its key includes the membership fingerprint
and the stock-history manifest state. A stock-history manifest change
invalidates only the dynamic price projection; it does not rebuild static
Theme membership.

The cache is not a source of truth. Source files remain authoritative, and
artifact writes are atomic JSON writes. No pickle or untrusted deserialization
is used.
