# Acquisition and Recovery

`DhanIntradayProvider` is lazy and bounded. It never constructs a client or
calls the provider until complete credentials are present. Historical calls
are date/interval/identity scoped. `IntradayParquetStore` is idempotent and
preserves the prior partition on failure. A later source-final candle can
replace a provisional live row at the canonical key with provenance retained.

The next operational step is a controlled representative validation after a
credential and entitlement gate, not an automatic full-market backfill.
