# Performance

Representative local benchmark on Python 3.11.9, Windows, Delhi timezone/location, canonical Swiss Ephemeris path:

| Range | Raw segments | Merged windows | Wall time |
|---|---:|---:|---:|
| 7 days | 20 | 4 | approximately 0.45 seconds |

The result reports `wall_ms` and `segments_evaluated`. No persistent cache was added. The bounded range and 20-result maximum prevent unbounded execution. No pathological loop was observed.
