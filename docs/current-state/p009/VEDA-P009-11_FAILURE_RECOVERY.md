# Failure Recovery

P009 extends restart safety and provider failure handling.

Implemented controls:
- stale runs remain recoverable through the existing platform bootstrap;
- worker execution uses a persisted lease;
- provider auth failures enter cooldown;
- temporary provider failures degrade the provider and allow fallback.

The runtime fails conservatively when persistence or provider execution cannot be trusted.
