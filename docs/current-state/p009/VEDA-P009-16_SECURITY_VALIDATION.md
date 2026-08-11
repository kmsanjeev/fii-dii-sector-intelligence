# Security Validation

P009 keeps the P006 and P007 trust boundary intact.

Implemented protections:
- unsafe schemes rejected;
- localhost/private-network targets rejected before retrieval;
- prompt-injection markers treated as source content, not instructions;
- provider auth failures enter cooldown instead of infinite retry;
- external providers are opt-in through environment configuration.

This phase does not weaken Admin approval or Approved Core promotion boundaries.
