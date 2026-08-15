# P015-RX Existing D4 Audit

Previous D4 routing used `KundliEngine._varga_sign(..., method="general")`. That shared fallback starts odd signs from the source sign and even signs from the 7th sign. It was used by D4 and other generic Vargas, so it was not deleted globally. D4 routing is now narrow and explicit.

Callers: the existing `_divisional_charts` path and the P015 canonical Varga mirror. Existing output shape is preserved.

