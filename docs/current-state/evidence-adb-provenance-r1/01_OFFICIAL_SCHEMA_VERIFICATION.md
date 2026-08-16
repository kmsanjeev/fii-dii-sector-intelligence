# Official schema verification

The official [ADB export readme](https://www.astro.com/adbexport/00_readme.htm) identifies the free C sample and says the current export contract/full download is unavailable during 2026. The official [XML export format](https://www.astro.com/astro-databank/Help%3AXML_export_format) defines:

- `ctimetype` as the time type/time-system field, not birth-time accuracy.
- `time_unknown` as the safeguard making a `12:00` value hypothetical for approximate positions.
- `itimeacc` and `stimeacc` as separate time-accuracy fields.
- `bdata_alt` as an optional alternative birth-data block.
- `datatype/@dsc` as the structured data-source code, with the documented source classes.

Observed sample fields were parsed from the XML attributes, not inferred from formatted clock text. Source-code meanings were checked against the official [DataSource reference](https://www.astro.com/astro-databank/Help%3ADataSource). The sample's current export contains 6,036 records, while the readme documents 5,866; that discrepancy remains explicitly reported.
