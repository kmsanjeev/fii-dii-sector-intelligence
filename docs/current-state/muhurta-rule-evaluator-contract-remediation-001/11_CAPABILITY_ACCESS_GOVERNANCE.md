# Capability and Access Governance

VEDA separates technical capability from deployment access:

```text
capability_state = IMPLEMENTED_VALIDATED
access_state     = ENABLED
```

Implemented and validated capability is enabled by default. A future
configuration layer may disable a feature, module, activity, role, deployment,
or permission tier without changing source truth, calculation facts, or rule
contracts. No configuration UI or authentication/authorization work is part of
this activity.

Current Muhurta states are technical readiness states, not permanent subject
bans:

- Business/Education: `PARTIAL_MACHINE_CONTRACT`; recommendation runtime not
  ready.
- Religious ceremony: `SOURCE_HARDENING_REQUIRED` and not yet engine-ready.
- Marriage, medical, legal and financial timing: `NOT_YET_CONTRACTED` or
  `NOT_YET_ENGINE_READY`; no rules implemented here.

Caution and professional consultation qualify future outputs. They do not
remove the underlying subject from VEDA's future capability roadmap.
