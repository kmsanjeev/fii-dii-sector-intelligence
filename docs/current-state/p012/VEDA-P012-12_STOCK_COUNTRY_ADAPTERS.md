# Stock & Country Adapters

The stock and country adapters preserve existing hard-coded offset behavior by normalizing with explicit offsets inside the runtime profile.

This keeps the P004 DST and historical-time conditions visible rather than silently replacing them with zoneinfo-derived semantics.
