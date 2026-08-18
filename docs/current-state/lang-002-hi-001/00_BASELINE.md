# VEDA-LANG-002-HI-001 — Baseline

Starting commit: `a1f268e1a4142468224c2e08019ecdcf1419fd31` on `main`.

The parent LANG-002 foundation is implemented/frozen as a presentation-only
boundary. It contains one canonical English locale with 33 governed term IDs
and 16 governed messages (49 keys total). The only pre-existing tracked edit
is `data/reference/city_coords_cache.csv`; it is unrelated, preserved, and
excluded from staging.

HI-001 reuses the parent registry, locale loader, fallback chain, structured
fact/display separation, source-citation preservation, and UTF-8 serializer.
It adds only the authorized Hindi resource pack, localized display aliases,
tests, review artifacts, and governance synchronization.

Preserved states: LANG-001 implemented/frozen; P032 recommendation layer
inactive; Tara Bala/Chandra Bala research-only; Ashtakavarga implemented but
unvalidated; D20 calculation partially validated and interpretation not
validated; prediction/PRED-M4/ML/RAG unchanged; COMM-002 and GROUP-001
pending.
