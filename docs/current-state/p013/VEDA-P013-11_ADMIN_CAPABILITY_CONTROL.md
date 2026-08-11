# Admin Capability Control

The framework is designed so Admin control can supervise:

- research start / continuation
- shadow entry
- activation
- pause
- rollback

P013 keeps the implementation fail-closed: non-Admin callers cannot mark a capability active by bypassing lifecycle gates.
