# Performance validation

The implementation scans the file names in the local F&O directory but reads only the bounded latest sessions required for the current EOD projection. A process-local cache is invalidated by selected file path/mtime/size and symbol scope. On the validation workstation, the independent direct-service measurement over five bounded files was:

| Sample | Observed |
|---|---:|
| First construction (cold) | 16.840 s |
| Warm samples | 0.186, 0.193, 0.116, 0.097, 0.122 s |
| Warm p50 | 0.122 s |
| Warm p95 (max of five) | 0.193 s |

The first live route construction is therefore intentionally treated as a bounded cold-start cost; subsequent same-snapshot calls are cache hits. No provider calls were added.
