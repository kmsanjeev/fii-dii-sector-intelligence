# Post-remediation benchmark

Measurements were taken on 2026-08-21 with the existing current evidence.

| Path | Result |
|---|---:|
| FII process import/startup | approximately 1.34s |
| FII first summary with valid artifacts | approximately 0.34s internal |
| FII command startup plus first summary | approximately 1.92s |
| Warm summary p50 | 0.081s |
| Warm summary p90 | 0.139s |
| Warm summary p95 | 0.192s |
| Warm summary max | 0.204s |
| Small Theme detail, 5 members | 0.002–0.004s internal |
| Medium Theme detail, 178 members | 0.002–0.004s internal |
| Large Theme detail, 670 members | 0.004–0.007s internal |
| FII HTTP catalogue | 0.38s |
| FII HTTP summary | 0.15s |
| FII HTTP detail | 0.02–0.08s |
| FII HTTP stock→Theme lookup | 0.02s |
| VEDA natural Theme query, first | 1.236s |
| VEDA natural Theme query, warm | 0.350s |

The offline cache build took approximately 27.0s on a cold local artifact.
That work is now explicit and outside the interactive request path.
