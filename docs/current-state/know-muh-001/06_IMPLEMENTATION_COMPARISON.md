# Implementation Comparison

| Current behavior | Source comparison | Decision |
|---|---|---|
| Solar-day facts | Engineering foundation, not classical rule | PLATFORM_EVIDENCE; preserved |
| Birth Panchanga display | Not electional selection | MATCH to existing boundary |
| Event taxonomy labels | Platform contract only | PLATFORM_ONLY |
| Nakshatra/tithi/karana source registry | Scoped classical support | VALIDATED_KNOWLEDGE, inactive |
| Tarabala/Chandrabala | No verified executable formula | UNVERIFIED / research candidate |
| Recommendations/scoring | No production behavior | NOT_IMPLEMENTED |

Material implementation mismatch: none, because no source-backed rule was
activated into production behavior.
