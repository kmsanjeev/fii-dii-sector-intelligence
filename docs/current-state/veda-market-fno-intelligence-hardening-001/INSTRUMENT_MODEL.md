# Instrument model and source mapping

| Source code | Instrument class | Underlying type | Authority |
|---|---|---|---|
| `STF` / `FUTSTK` | FUTURE | STOCK | observed current/legacy NSE schema |
| `IDF` / `FUTIDX` | FUTURE | INDEX | observed current/legacy NSE schema |
| `STO` / `OPTSTK` | OPTION | STOCK | observed current/legacy NSE schema |
| `IDO` / `OPTIDX` | OPTION | INDEX | observed current/legacy NSE schema |
| anything else | UNKNOWN | UNKNOWN | preserved, not inferred |

Current files use `TradDt`, `FinInstrmTp`, `TckrSymb`, `XpryDt`, `OpnIntrst`, `ChngInOpnIntrst` and related fields. Legacy files use `TIMESTAMP`, `INSTRUMENT`, `SYMBOL`, `EXPIRY_DT`, `OPEN_INT`, `CHG_IN_OI` and related fields. The normalized model preserves absent values as null.

Source witness: NSE's historical F&O data-details document identifies Date,
Symbol, Instrument, Expiry date, Option Type, Strike, closing price, open
interest, total contracts and total traded value as distinct fields. NSE's
current derivatives reports page lists F&O Bhavcopy and the post-2024 UDiFF
Common Bhavcopy separately; the local archive therefore retains explicit
schema-era metadata rather than pretending one universal layout.
