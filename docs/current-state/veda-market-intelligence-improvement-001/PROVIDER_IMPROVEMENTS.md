# Provider improvements

The formal provider contract now distinguishes:

1. data status (`state`),
2. latest usable evidence date (`as_of`),
3. source label,
4. last successful local update,
5. limitations and unavailable optional inputs.

This is provider-local metadata, not a claim of external source authority.
The source label identifies FII-DII local datasets without exporting their
contents. VEDA receives only the formal read-only response.

The implementation keeps old response fields and adds metadata, so existing
dashboard/reporting consumers remain compatible. Missing numeric values are
represented as null rather than manufactured zeros.
