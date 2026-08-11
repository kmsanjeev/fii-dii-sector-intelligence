# VEDA-P010 Versioning and Supersession

P010 extends governed version handling to promoted Core Knowledge.

Implemented states:
- `CURRENT`
- `SUPERSEDED`
- `DEPRECATED`
- `WITHDRAWN`

Behavior:
- new promoted current versions supersede prior current versions non-destructively;
- prior versions retain linkage to the replacing core record;
- supersession reason and promotion linkage are preserved;
- retries remain idempotent because core IDs, promotion IDs, and rule/source identities are controlled explicitly.

The synthetic merge test proves:
- existing current core can be superseded;
- previous core remains queryable;
- new core becomes current without destructive overwrite.
