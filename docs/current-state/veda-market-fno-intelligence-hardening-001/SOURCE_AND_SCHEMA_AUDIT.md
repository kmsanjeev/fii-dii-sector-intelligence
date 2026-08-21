# Source and schema audit

Primary source witnesses inspected:

1. NSE, *All Reports — Derivatives*, accessed 2026-08-21. It distinguishes
   the discontinued pre-08-Jul-2024 F&O Bhavcopy/CSV from the current UDiFF
   Common Bhavcopy and separately lists participant-wise OI/volume reports.
2. NSE, *Historical Data Dissemination of Future and Options Segment*,
   `archives.nseindia.com/content/press/Data_Details_F_n_O.pdf`, pages 2–3,
   accessed 2026-08-21. It defines legacy Date, Symbol, Instrument, Expiry,
   Option Type, Strike, price, OI, contracts and traded value fields and names
   `FUTSTK`, `OPTIDX` and related descriptors.
3. NSE, *Market Feed — FO Data Structure*, `Snapshot_MDR_RT_FAO_V1.7.pdf`,
   page 20, accessed 2026-08-21. It states the Bhavcopy is an EOD file
   generated around 17:00 IST and lists `FUTSTK`, `OPTSTK`, `FUTIDX` and
   `OPTIDX` legacy instrument names.

Local evidence was sampled from the first, middle, previous and latest files:
6,452 files total; current `STO`, `IDO`, `STF`, `IDF`; legacy `FUTIDX`,
`FUTSTK`, `OPTIDX`, `OPTSTK`. The code preserves unknown source codes as
UNKNOWN and does not infer undocumented categories.
