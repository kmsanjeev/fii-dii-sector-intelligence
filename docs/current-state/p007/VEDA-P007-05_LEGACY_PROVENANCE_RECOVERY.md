# VEDA-P007 Legacy Provenance Recovery

Pilot B exercises the provenance-recovery path for legacy rule `VEDA-P005-LGC-0001`.

## Legacy Rule

- domain: `YOGA`
- rule id: `VEDA-P005-LGC-0001`
- current legacy behavior: simplified Pancha Mahapurusha-family detection

## Research Flow

1. Normalize the legacy rule into a research claim.
2. Search governed corpus and discovery-only upload corpus.
3. Extract discovery evidence with explicit `REFERENCE_NOT_VERIFIED` metadata.
4. Create a reviewable provenance candidate.
5. Reject the candidate when discovery-only evidence is still insufficient.
6. Re-run the same mission and enrich the rejected archived candidate instead of creating a duplicate.

## Pilot Result

- first run: `4` sources, `1` candidate, `3` duplicate enrichments
- rejected rediscovery: same candidate retained, final evidence ids `8`, final support count `4`
- no second admin queue item created after the archive-aware dedupe fix
