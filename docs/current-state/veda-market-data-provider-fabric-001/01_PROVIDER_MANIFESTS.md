# Provider manifests and capability policy

The canonical implementation is `engines.providers.fabric`. Provider IDs are
stable policy identifiers, not credentials or runtime proof.

| Provider | Type | Capabilities | Authority/state |
|---|---|---|---|
| `local-governed` | `LOCAL_GOVERNED` | EOD equity/F&O history, portfolio import | Internal governed local stores |
| `dhan` | `BROKER` | intraday, LTP/quote/stream/depth, OI/options, portfolio read | Official DhanHQ; entitlement/runtime validation required |
| `zerodha-kite` | `BROKER` | historical/intraday, quote/stream/depth, portfolio read | Official Kite Connect; unvalidated in this activity |
| `hdfc-sky` | `BROKER` | manifest only for historical/live/portfolio candidates | Official HDFC Sky portal; policy/scope validation required |
| `csv-import` | `FILE_IMPORT` | portfolio snapshot import | User-provided file; no market feed |
| `yfinance` | `PUBLIC_COMPATIBILITY` | EOD equity compatibility | Local research/personal-use compatibility only |
| `nselib` | `RESEARCH_CANDIDATE` | EOD equity/F&O candidate | No production authority assigned |
| `nsepython` | `RESEARCH_CANDIDATE` | EOD/intraday candidate | No production authority assigned |

The resolver requires capability match plus connection state, authorization,
entitlement and health. It never maps a missing live provider to EOD data.
