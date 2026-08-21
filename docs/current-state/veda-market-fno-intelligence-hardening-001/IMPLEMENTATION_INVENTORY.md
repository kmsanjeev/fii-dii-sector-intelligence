# VEDA-MARKET-FNO-INTELLIGENCE-HARDENING-001 — Implementation inventory

Status: IMPLEMENTED / FROZEN WITH CONDITIONS

The existing `engines/intelligence/fno_engine.py` remains the daily stage and now delegates its normalization/projection to `backend/services/governed_fno_intelligence.py`. NSE acquisition remains in `engines/acquisition/nse_fno_acquisition_engine.py`; no second downloader or second F&O platform was created. The local archive contains 6,452 files from 2000-06-12 through 2026-08-19. Historical schemas are not homogeneous.

Changed runtime surfaces:

- FII: governed `fno-intelligence-1.0`, compatibility CSV/JSON outputs, `/api/fno/summary`, `/api/fno/stocks/{symbol}` and `/api/fno/indices/{index}`.
- FII: stock, cross-layer and read-only portfolio contracts receive additive descriptive F&O context.
- VEDA: read-only `market.fno.intelligence` proxies `/api/fno/summary`.

No VEDA-side calculation, participant options attribution, trading, intraday, ML, PRED, EMP, RAG, Jyotish, Theme-history or BEBOS behavior changed.
