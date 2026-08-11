# VEDA-P010 Rollback and Recovery

Rollback is implemented as governed recovery, not destructive deletion.

Rollback behavior:
- promoted current versions are marked `WITHDRAWN`;
- previous versions are restored to `CURRENT` when available;
- approved-core docs are rewritten from the surviving current store view;
- index sync runs again after rollback;
- rollback emits its own durable record and ledger event.

If no previous current version exists, the candidate returns to `BLOCKED` rather than falsely claiming a restored ready state. This exact case is covered by the P010 admin API rollback test.
