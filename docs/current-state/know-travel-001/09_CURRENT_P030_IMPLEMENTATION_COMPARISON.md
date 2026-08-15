# Current P030 Implementation Comparison

| P030 element | Classification | Engineering finding |
|---|---|---|
| Travel != relocation | PLATFORM_ONLY / MATCH | Preserved exactly |
| Foreign travel != foreign residence | PLATFORM_ONLY / MATCH | Preserved exactly |
| Residence != permanent settlement | PLATFORM_ONLY / MATCH | Preserved exactly |
| Away from birthplace != foreign nation | PLATFORM_ONLY / MATCH | Preserved exactly |
| Opportunity != event | PLATFORM_ONLY / MATCH | Preserved exactly |
| Structural promise != timing | PLATFORM_ONLY / MATCH | Preserved exactly |
| Dasha/transit convergence | PLATFORM_ONLY with classical partial support | No code change |
| 3rd/4th/7th/9th/12th claims | Research/reference inputs only | No material mismatch because P030 does not calculate them |
| Rahu foreign settlement | Rejected universal claim | Not encoded |
| D4 interpretation | Gated | No change |
| P021/P023/P024/P029 context | Platform association | No causal guarantee added |
| Immigration/legal/financial/career advice | Blocked output | No leakage found in focused P030 tests |

Overall: `MATCH` for P030 governance architecture; `PLATFORM_ONLY` for distinctions; `UNVERIFIED` for unsupported classical extensions. `MATERIAL_MISMATCH = 0`; `P030-R1_REQUIRED = NO`.
