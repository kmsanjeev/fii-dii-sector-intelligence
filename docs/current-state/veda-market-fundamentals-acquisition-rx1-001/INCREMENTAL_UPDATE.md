# Incremental update and idempotency

Before the controlled run the quarterly result store contained `32395` rows
for `2333` symbols. After the first repaired run it contained `32403` rows,
an increase of `8` records with no new reporting-period maximum. The current
maximum period remains `2026-03-31`.

The second identical live run returned `32403` rows and `2333` symbols. The
canonical CSV SHA-256 and UTC modification time were unchanged:

```text
SHA-256: 209447D261B8A2B3CEBA91843BFF2AEC66DF8E6E2BFB0D9589D9B41EE42F6095
```

This proves no unnecessary rewrite and stable normalized output. The engine
still rechecks the authorized recent source windows on each invocation so a
new issuer filing can be discovered without requiring a new label.
