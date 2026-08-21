# Direct-flow decision

## Stock-level FII/DII gate

Decision: `NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE`.

The local raw tape is direct disclosed bulk/block activity, but it is not a
complete daily FII/DII stock-flow ledger. The source has client names and a
derived keyword classification. The fallback `RETAIL` label is not treated as
reported participant identity. Market FII/DII aggregates are not attributed
to a stock.

## Sector-level gate

Decision: `NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE`.

No direct sector FII/DII feed is persisted. A future aggregation may be
considered only if symbol identity, sector mapping, date semantics, coverage
and aggregation rules are independently governed. No such aggregation is
claimed by this activity.

## What is available

The stock contract can report disclosed deal activity and quarterly ownership
change independently. It never upgrades either into “FII accumulation” or a
daily sector-flow statement.
