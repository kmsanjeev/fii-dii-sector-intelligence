# VEDA-P004 Timezone Validation

Path classification:

| Path | Classification | DST Handling | Historical Handling | Evidence |
| --- | --- | --- | --- | --- |
| `PERSONAL_KUNDLI` | `FIXED_OFFSET` | `CALLER_DEPENDENT` | `CALLER_DEPENDENT` | timezone_offset_hours is converted into a fixed tzinfo offset and then to UTC. |
| `REST_HUMAN` | `FIXED_OFFSET` | `CALLER_DEPENDENT` | `CALLER_DEPENDENT` | HumanKundliRequest accepts tz_offset only; KundliEngine._to_jd subtracts that offset directly. |
| `STOCK_KUNDLI` | `HARDCODED_OFFSET` | `ABSENT` | `ABSENT` | compute_stock resolves exchange tz names through KundliEngine._tz_offset() fixed mappings. |
| `COUNTRY_KUNDLI` | `HARDCODED_OFFSET` | `ABSENT` | `ABSENT` | Country charts embed fixed tz_offset values directly in COUNTRY_CHARTS. |

Boundary and DST validation cases:

| Case ID | Path | Zone | Assumed Offset | Zoneinfo Offset | UTC Delta (h) | Lagna Delta (deg) | Result |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `TZ-NYSE-WINTER` | `STOCK_KUNDLI` | `America/New_York` | `-5.0` | `-5.0` | `0.0` | `0.0` | `VALIDATED` |
| `TZ-NYSE-SUMMER` | `STOCK_KUNDLI` | `America/New_York` | `-5.0` | `-4.0` | `1.0` | `11.885204` | `DISCREPANT` |
| `TZ-LSE-SUMMER` | `STOCK_KUNDLI` | `Europe/London` | `0.0` | `1.0` | `1.0` | `10.507945` | `DISCREPANT` |
| `TZ-ASX-SUMMER` | `STOCK_KUNDLI` | `Australia/Sydney` | `10.0` | `11.0` | `1.0` | `12.446098` | `DISCREPANT` |
| `TZ-PAK-1947` | `COUNTRY_KUNDLI` | `Asia/Karachi` | `5.5` | `5.5` | `0.0` | `0.0` | `VALIDATED` |
| `TZ-IND-1947` | `COUNTRY_KUNDLI` | `Asia/Kolkata` | `5.5` | `5.5` | `0.0` | `0.0` | `VALIDATED` |

Key observations:

- Human paths can still be mathematically correct when the caller supplies the correct historical fixed offset.
- Stock and country paths are not caller-correctable because offsets are derived internally.
- Sampled summer exchange openings drift by exactly one UTC hour under the current fixed-offset mappings.
