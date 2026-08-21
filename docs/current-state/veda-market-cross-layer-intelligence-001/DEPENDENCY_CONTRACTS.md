# Dependency contracts

| Layer | Contract | Owner | Current use |
|---|---|---|---|
| Market | existing market context/regime | FII-DII | Market state, breadth, risk context |
| Institutional | `institutional-flow-1.1` | FII-DII | Cash/F&O participant context and dates |
| Sector | `sector-rotation-1.1` | FII-DII | Leadership, rotation, breadth and persistence |
| Stock | `stock-intelligence-1.1` | FII-DII | Trend, momentum, volume, relative strength and context |
| Corporate/fundamental | existing dated provider datasets | FII-DII | Structural/event context only |

No formulas were copied into the composition layer. Broad participant data
remains `MARKET_LEVEL_CONTEXT_ONLY` unless the stock contract supplies a
stronger governed deal/ownership scope.
