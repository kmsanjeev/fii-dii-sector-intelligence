# City Cache Provenance

Previous state: one unstaged row in `data/reference/city_coords_cache.csv`.

| Check | Result |
|---|---|
| Row | `barh,25.450977,85.700249,"Barh, Patna, Bihar, 803213, India",nominatim,2026-08-18` |
| Existing history | The tracked cache was introduced by the project reference-data commit; `barh` is not in prior history. |
| Generation source | `engines/ai/chatbot/tools/geocoder.py` explicitly appends successful Nominatim results with `source=nominatim` and `added_on` date. |
| Format | Matches the cache schema and the generator write format. |
| Plausibility | Coordinates and resolved name identify Barh in Bihar and are internally consistent. |
| Stale/accidental evidence | No evidence of staleness or malformed data was found. |
| Governance result | `VALID_PROJECT_CHANGE_SHOULD_COMMIT` |

The row is included in this governed commit as a documented reference-data
change. It is not provider research data, raw ADB data, or a calculation result.
