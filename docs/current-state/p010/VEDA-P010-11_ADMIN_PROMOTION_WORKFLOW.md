# VEDA-P010 Admin Promotion Workflow

P010 extends the P008 Research Control Centre with a second explicit governance step after approval.

Admin workflow is now:
1. review candidate evidence;
2. approve or approve with conditions;
3. candidate enters `PROMOTION_READY`;
4. run promotion preflight;
5. inspect blockers, warnings, and required actions;
6. explicitly select `Promote to Core Knowledge`;
7. optionally roll back a completed promotion.

The UI now shows:
- promotion state;
- latest preflight status;
- latest promotion status;
- core version count;
- blocking reasons and warnings;
- promotion notes;
- rollback reason and history.

Approval and promotion remain separate actions by design.
