# VEDA-MARKET-FNO-INTELLIGENCE-HARDENING-001 - Final acceptance

Decision: `VEDA_MARKET_FNO_INTELLIGENCE_HARDENING_OPERATIONAL_WITH_CONDITIONS`

The governed F&O projection is operational for bounded, descriptive EOD use.
Nearest expiry and most-active selection are separate; roll transitions suppress
cross-contract price/OI interpretation; five-session OI is withheld when the
selected contract is not continuous; stock and index PCR scopes are explicit;
ordinary bhavcopy never becomes participant-wise stock-option attribution.

Observed validation:

- Local source inventory: 6,452 F&O files; latest observed file/date
  `fo_20260819.csv` / `2026-08-19`; current instrument codes `STO`, `IDO`,
  `STF`, `IDF`; legacy codes `FUTIDX`, `FUTSTK`, `OPTIDX`, `OPTSTK`.
- Governed output: 214 selected futures records, separate stock/index PCR,
  source status and explicit unsupported-feature states.
- FII full suite: 1,359 passed; the initial API snapshot mismatch was resolved
  by recording the three canonical governed F&O routes (156 paths / 169
  operations) and the affected contract test then passed 3/3.
- VEDA platform full suite: passed; only dependency deprecation warnings.
- Real HTTP: FII F&O routes and the VEDA provider query returned valid
  `fno-intelligence-1.0` data.
- Determinism: repeated direct-service digest
  `2b6f562d15ca447732c0701c1ef2ec6ec3edee80257149f9c4ef61573279f` matched.
- Performance: cold 16.840 s; warm p50 0.122 s; warm p95 0.193 s on the
  validation workstation.
- Scope: no RAG, PRED, EMP, ML, Jyotish, Intraday, Theme-history, automated
  trading or BEBOS changes.

Conditions retained:

1. F&O is EOD and source-conditioned; it is not an intraday feed.
2. Participant-wise options attribution, Greeks and Max Pain remain unsupported.
3. Positional/Swing intelligence remains the authorized next programme and is
   not started here.
4. Existing unrelated generated/data changes remain unstaged and preserved.
