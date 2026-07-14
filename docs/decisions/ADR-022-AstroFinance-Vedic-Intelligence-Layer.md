# ADR-022 — AstroFinance / Vedic Intelligence Layer
Status: Accepted
Date: 2026-07-15

## Context

Prior to this ADR, five astrology-related code paths had been built and
wired into production (`daily_refresh.py` schedules `AF_astro_engine`,
`KU_kundli_engine`, `KU_gann_engine`) without ever going through the
project's own governance process: no `docs/modules/ASTRO.md`, no ADR, no
entry in `engines/CLAUDE.md`'s directory index or `MODULE_REGISTRY.md`.
`MASTER_ROADMAP.md` referenced a file path (`engines/astro/
planetary_intelligence_layer.py`) that never existed — a symptom of the
feature having grown outside the documentation loop.

A research pass comparing the platform's astrology implementation against
classical predictive-astrology methodology (anchored on *Star Guide to
Predictive Astrology*, Pandit K.B. Parsai) surfaced two real defects
alongside a set of methodology gaps:

1. **Correctness bug**: `astro_engine.py` computed planetary longitudes
   as tropical (no ayanamsha correction) but labeled the resulting signs
   with Vedic/sidereal names — every sector's "planet in sign X" reading
   was off by the full ~24° Lahiri ayanamsha offset.
2. **Engine duplication**: the stock/company Kundli (`kundli_engine.py`,
   Swiss Ephemeris, exact ayanamsha, True Node) and the personal-chat
   Kundli (`kundli_calculator.py`, PyEphem, a linear-approximation
   ayanamsha, mean node) were two independent, non-shared calculation
   pipelines that could disagree on the same chart by up to ~1.5-2°.
3. An orphaned ASTRO RAG index (3,173 FAISS vectors) with zero matching
   rows in `documents.jsonl` — built from source PDFs that no longer
   exist on disk, and unreachable regardless since `retriever.py`'s
   domain auto-detection never routes to "ASTRO".
4. `kundli_signals.csv`, `gann_signals.csv`, and the per-symbol Kundli
   JSON cache had never been bulk-generated — every stock Kundli view
   was computed live, with no historical archive to validate against.
5. Methodology gaps against the classical/Parsai framework: no Bhava Phal
   (full 12-house prediction — the book's own three-part structure is
   fundamentals -> houses -> planet-in-house effects), no Ashtakavarga,
   no Shadbala (planetary strength), no Varshphal. The stock Kundli score
   also has zero influence on `trade_conviction_engine.py` — the
   platform's actual recommendation engine — making the whole feature a
   standalone display, not yet a decision input.

## Decision

1. **Retroactively document** the existing five-engine astrology layer as
   a first-class platform module (this ADR + `docs/modules/ASTRO.md` +
   `MODULE_REGISTRY.md` Module 19 + `engines/CLAUDE.md` directory entries).

2. **Fix the sidereal bug** in `astro_engine.py` by delegating sign
   placement to Swiss Ephemeris's native `FLG_SIDEREAL` calculation (same
   path `kundli_engine.py` uses) instead of PyEphem tropical longitude
   minus a manually-subtracted ayanamsha. This also fixed a second,
   independent bug: PyEphem's `Ecliptic(epoch=J2000)` is not precessed to
   the date, which alone introduced a ~0.36° error as of 2026 — invisible
   until cross-checked directly against `kundli_engine.py`.

3. **Unify the two Kundli calculators**: `kundli_engine.py` remains the
   canonical Swiss-Ephemeris calculation core (positions, Ascendant,
   ayanamsha). `kundli_calculator.py` keeps its richer personal-chart
   feature set (Panchang, doshas, Lal Kitab remedies, city geocoding,
   functional-nature/yogakaraka analysis, formatted report) but now
   calls into `KundliEngine` for all position/Ascendant/ayanamsha math
   rather than maintaining a second implementation. Verified: both paths
   now produce identical Lagna/planet positions for identical input.

4. **NSE listing-time approximation is retained, and is now cited, not
   assumed**: the stock Kundli's `10:00 IST` listing-moment default was
   investigated (Phase ASTRO-FIX spike) and confirmed to be NSE's actual,
   SEBI-mandated commencement time for normal trading on every new
   listing, following the mandatory Special Pre-Open Session (09:00-09:45
   IST price discovery). It is not an arbitrary placeholder.

5. **Bulk-generate** `kundli_signals.csv` (2,053 symbols) and
   `gann_signals.csv` (2,052 symbols) so future sessions have a real
   archive instead of live-only computation, and so a future signal-
   efficacy pass (see Roadmap below) has history to backfill against.

6. **Retire, not delete**, the orphaned ASTRO FAISS index
   (`faiss_ASTRO.index` -> `.retired`) — source PDFs are unavailable on
   this machine; re-ingestion remains possible if located later, and the
   rename is fully reversible. Left `ASTRO` in `faiss_indexer.py`'s
   `DOMAINS` list since the domain concept is legitimate, just currently
   empty.

## Roadmap (proposed, not yet built — tracks the research-brief gap analysis)

| Phase | Scope |
|-------|-------|
| ASTRO-FIX | This ADR's scope — correctness, unification, governance (DONE 2026-07-15) |
| ASTRO-BHAVA | Full 12-house Bhava Phal engine, shared between stock and personal charts |
| ASTRO-INTEGRATE | Wire the unified Kundli score into `trade_conviction_engine.py` as a labeled experimental factor |
| ASTRO-STRENGTH | Ashtakavarga (bindu house strength) + Shadbala (6-fold planetary strength) |
| ASTRO-TIMING | Deeper Gochara (Moon-sign transits, Vedha, Sade Sati) + Varshphal (annual/Tajika chart) |
| ASTRO-VALIDATE | Backfill historical scores into the SA-1 `score_snapshot`/`signal_efficacy.csv` framework; replace ASTRO-INTEGRATE's placeholder weight with an efficacy-derived one |
| ASTRO-UI | North/South Indian chart rendering; dedicated personal-Kundli input form |

## Consequences

**Positive:**
- Sector transit signs and stock/personal natal charts are now internally
  consistent — the platform can no longer disagree with itself about
  where a planet is.
- One calculation core instead of two reduces future maintenance surface
  and eliminates an entire class of "which engine is right" bugs.
- `kundli_signals.csv`/`gann_signals.csv` existing as real files unblocks
  future efficacy validation and removes live-computation latency from
  the stock Kundli card.
- The feature is now discoverable through the same governance docs as
  every other module, closing a real blind spot (five production engines
  were invisible to `engines/CLAUDE.md`'s own directory index).

**Negative:**
- The astrology signal remains disconnected from real recommendations
  until ASTRO-INTEGRATE/ASTRO-VALIDATE are built — still a display-only
  feature as of this ADR.
- `pyswisseph`/`ephem` are now hard dependencies (`requirements.txt`) for
  three engines; a clean install without them will fail those specific
  engines, though the rest of the platform is unaffected.
- The ASTRO RAG domain is currently empty; any future re-ingestion also
  needs a small fix to `retriever.py`'s `DOMAIN_KEYWORDS` (never routes
  to ASTRO today) to actually be reachable.

## Related ADRs

- ADR-012 — Research Before Development (basis for the gap-analysis pass this ADR follows)
- ADR-014 — Module-Driven Development
- ADR-015 — Documentation Mandatory Before Release (this ADR closes a retroactive gap against that rule)
