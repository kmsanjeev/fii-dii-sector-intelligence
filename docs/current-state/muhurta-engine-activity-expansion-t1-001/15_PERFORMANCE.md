# Performance

Observed on the local Python 3.11.9 environment with canonical P032/Kundli
transition facts:

| Activity | Candidate | 7-day search | 31-day search |
|---|---:|---:|---:|
| Vehicle | 1.2-1.5 ms | 163.407 ms | 822.532 ms |
| Consecration | 1.1-2.7 ms | 203.497 ms | 742.895 ms |

These are observations, not an arbitrary SLA. No provider calls were added.
