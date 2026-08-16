# Ledgers and Leakage Controls

The future observation ledger records participant, event family, observation
window, registration/resolution timestamps, resolution status/source and data
version. A prediction-ledger interface is designed only conceptually; no real
predictions are executed. Frozen snapshots, immutable registration records and
method/contract hashes prevent outcome-window edits and retroactive leakage.
