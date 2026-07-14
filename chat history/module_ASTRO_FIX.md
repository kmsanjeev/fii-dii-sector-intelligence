# Module Log — Phase ASTRO-FIX: Astrology Layer Correctness, Unification & Governance

**Date:** 2026-07-15
**Status:** COMPLETE
**Version:** 4.47.0

## User Request

"Since Veda should work..." (unrelated prior phase, completed separately)
then: "Today, I want you to do a deep research on the predictive astrology
based on available artifacts... Share me the research outcome and
accordingly we will plan our further development with a roadmap." Followed
by: "now build a roadmap to fix the known bugs and fill the gaps. Hopefully
this will give us more vibrant results. any inputs or suggestion from your
end?" Then: "start the fix."

## Process

1. Spawned a background codebase-audit agent to inventory every astrology-
   related engine, route, chatbot tool, RAG doc, and frontend surface with
   file:line precision.
2. Researched classical predictive-astrology methodology (Dasha/Gochara/
   Ashtakavarga/Vargas, 12-house significations, Shadbala) and financial/
   mundane astrology technique, plus the recommended book's actual scope
   (Star Guide to Predictive Astrology, Pandit K.B. Parsai — 3-part
   structure: fundamentals -> 12 houses -> planet effects per house).
3. Published a gap-analysis Artifact comparing the two against each other,
   with a 7-phase roadmap (ASTRO-FIX -> ASTRO-BHAVA -> ASTRO-INTEGRATE ->
   ASTRO-STRENGTH -> ASTRO-TIMING -> ASTRO-VALIDATE -> ASTRO-UI).
4. Confirmed astro/kundli have zero references in trade_conviction_engine.py
   — the astrology layer has never influenced real recommendations.
5. Got two open decisions resolved via AskUserQuestion: (a) investigate the
   NSE listing-time feasibility rather than assume it's arbitrary, (b) let
   ASTRO-INTEGRATE happen sooner as a labeled-experimental factor rather
   than strictly gating on ASTRO-VALIDATE — re-sequenced the roadmap
   accordingly.
6. User said "start the fix" — executed Phase ASTRO-FIX (this log).

## Bugs found and fixed

### 1. astro_engine.py: tropical longitudes labeled as sidereal

PyEphem's `Ecliptic(body, epoch=ephem.J2000).lon` is tropical; the code
subtracted nothing before assigning Vedic sign names. Every sector's
planet-in-sign reading was off by the full Lahiri ayanamsha (~24 degrees
in 2026). Verified by pinning both engines to the same exact instant and
diffing: before the fix, all 9 planets showed a uniform ~0.36 degree
offset from kundli_engine.py's output (a *second*, independent bug — see
below) and Rahu/Ketu showed a ~1.59 degree offset (mean vs true node).

Fix: replaced the entire position-computation method with direct Swiss
Ephemeris `swe.calc_ut(jd, planet_id, FLG_SIDEREAL | FLG_SPEED)` calls —
the same path kundli_engine.py already used — instead of hand-rolling a
tropical-then-subtract-ayanamsha pipeline in PyEphem. This incidentally
fixed bug #2 below for free, since it stopped touching PyEphem's
non-precessed J2000 epoch at all for sign placement.

### 2. astro_engine.py (subsumed by #1): PyEphem J2000-epoch precession error

Diagnosed while verifying fix #1: even after correctly subtracting a
date-of-epoch ayanamsha, a ~0.36 degree residual remained across all 9
planets uniformly. Root cause: `Ecliptic(epoch=J2000)` returns coordinates
referenced to the *fixed* J2000 equinox, not precessed to the date —
subtracting a date-of-epoch ayanamsha from a J2000-referenced longitude
leaves an error equal to accumulated precession since J2000 (~26 years x
~50.3"/year ~= 0.363 degrees as of 2026 — matches the observed residual
almost exactly). Fixed by the same rewrite as #1 (Swiss Ephemeris handles
precession internally).

### 3. Two independent Kundli engines could disagree by up to ~2 degrees

kundli_engine.py (stock/company/country charts): Swiss Ephemeris, exact
Lahiri ayanamsha via `swe.get_ayanamsa_ut()`, True Node.
kundli_calculator.py (personal chat charts): PyEphem, a *linear
approximation* Lahiri formula (`23.85306 + t*1.396`), mean-node formula
for Rahu/Ketu, and a hand-rolled Meeus Ascendant formula.

Verified before fixing: for the same instant, all 9 planets differed by
~0.36 degrees (same J2000-epoch bug as astro_engine.py, independently
present in this second file) and Rahu/Ketu by ~1.59 degrees (mean vs true
node) — i.e. the exact same two defect classes, duplicated across two
unrelated files.

Fix: `kundli_calculator.py` now imports `KundliEngine` and delegates
`_compute_positions()`, `_compute_lagna()`, and `_lahiri_ayanamsha()` to
it (module-level singleton instance, since `KundliEngine.__init__` only
sets a cheap, idempotent global sidereal mode). Everything downstream of
position math — Panchang, dosha detection, Lal Kitab remedies, yogas,
drishti, the formatted report, functional-nature/yogakaraka analysis —
was left untouched, since it's agnostic to how the underlying longitude
was computed. Removed the now-dead `_sidereal()`, the linear-ayanamsha
body (kept the function signature, delegated the body — zero call-site
changes needed for two of the three call sites), the mean-node formula
usage, and the now-unused `import math`.

Verified: `compute_stock('RELIANCE', ...)` via KundliEngine directly and
`compute_personal_kundli('15-08-1990', '14:30', 'Mumbai')` via the merged
kundli_calculator.py produce byte-identical Lagna/Sun/Moon sign+degree
for the same input where comparable. Full report generation (30k+ chars,
including Panchang, doshas, Lal Kitab, Sade Sati check, life-guide
summary) runs end-to-end with no exceptions.

## Spike: NSE 10:00 IST listing time

User asked to investigate rather than assume. Found via web research:
NSE's documented, SEBI-mandated "Special Pre-Open Session" for every new
listing runs price discovery 09:00-09:45 IST; normal continuous trading
(the stock's actual first tradeable moment at a market-discovered price)
commences at 10:00 IST, market-wide, for essentially every NSE IPO. The
existing hardcoded `ipo_hour=10` in kundli_engine.py's `EXCHANGES` dict
was therefore already correct — not an arbitrary guess as the earlier
audit had characterized it. Documented this with a full citation trail in
both the code comment and docs/modules/ASTRO.md, including the one known
exception (rare ceremonial "Muhurat" listings) as an unhandled edge case
for a future symbol-level override.

## Bulk archives generated

Neither `kundli_signals.csv` nor `gann_signals.csv` had ever been
bulk-run — both engines only ever ran on-demand per API request, with no
historical archive. Ran both (outside market hours, 21:08 IST, per
guardrail G-A-04): `KundliEngine.run()` processed 2,053 symbols in 18.8s,
`GannEngine.run()` processed 2,052 symbols in 1.5s (depends on
kundli_signals.csv + price_momentum.csv).

## RAG index retired

`faiss_ASTRO.index` (3,173 vectors) had zero matching rows in
`documents.jsonl` — built from 4 source PDFs at hardcoded Desktop paths
that don't exist on this machine (confirmed via a full-user-directory
filesystem search, zero hits). Also confirmed `retriever.py`'s
`DOMAIN_KEYWORDS` dict never routes any query to the ASTRO domain
regardless of index state, so the index was doubly unreachable. Renamed
both index files to `.retired` (reversible — not deleted) rather than
permanently removing, since `data/intelligence/rag_knowledge/` is
documented as rebuildable cache, not raw data.

## Governance gap closed

Five production-wired engines (scheduled in `daily_refresh.py`) had no
`docs/modules/` entry, no ADR, and no listing in `engines/CLAUDE.md`'s
directory index or `MODULE_REGISTRY.md` — a genuine blind spot against
the project's own documentation rules (ADR-015). Closed with:
- `docs/decisions/ADR-022-AstroFinance-Vedic-Intelligence-Layer.md`
- `docs/modules/ASTRO.md`
- `docs/governance/MODULE_REGISTRY.md` — new Module 19
- `engines/intelligence/CLAUDE.md` — active-engines table extended
- `engines/CLAUDE.md` — targeted fix to the (broadly stale) top-level
  directory map, astro engines added
- `docs/governance/MASTER_ROADMAP.md` — Phase AF entry's file-path
  reference corrected (previously cited a non-existent
  `engines/astro/planetary_intelligence_layer.py`)

## Files changed

See CHANGELOG.md Version 4.47.0 for the full file list.

## Not done in this phase

Bhava Phal, Ashtakavarga, Shadbala, Varshphal, Trade Conviction
integration, signal-efficacy validation, North/South Indian chart
rendering — all scoped in ADR-022's roadmap table, none built. Awaiting
user prioritization of the next phase (ASTRO-BHAVA is next in sequence
per the agreed roadmap).

## Verification performed

- Direct position cross-check between astro_engine.py and kundli_engine.py
  pinned to the identical instant (2026-07-15 12:00 UTC): max diff 0.004
  degrees across all 9 planets + Rahu/Ketu after the fix (was ~0.36-1.59
  degrees before).
- Direct cross-check between kundli_engine.py and kundli_calculator.py for
  identical birth data (15-08-1990, 14:30 IST, Mumbai): identical
  Lagna/Sun/Moon sign and degree.
- Full `compute_personal_kundli()` report generation with no exceptions,
  including all downstream sections (Panchang, doshas, Lal Kitab, Sade
  Sati, life guide).
- `compute_stock('RELIANCE', ...)` confirmed unaffected/working after
  kundli_engine.py's comment-only edit.
- `backend.routers.kundli` and `backend.main` both import cleanly after
  all changes.
- Both bulk jobs (KundliEngine.run(), GannEngine.run()) completed
  successfully with real output row counts confirmed by reading the CSVs.
- Confirmed no other code in the repo calls the internal functions that
  changed signature (`_compute_lagna`, `_compute_positions`,
  `_lahiri_ayanamsha`) outside kundli_calculator.py itself.
