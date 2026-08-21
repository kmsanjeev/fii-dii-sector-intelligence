# Stock and Cross-Layer Integration

`stock-intelligence-1.1` consumes Corporate as a bounded contextual section:

- contract version and announcement state;
- recent normalized events;
- scheduled events;
- source update/freshness;
- evidence quality, watch items and limitations.

`cross-layer-1.0` exposes this as `corporate_event_context`. It does not count
Corporate rows as institutional confirmation, fundamental proof, sector
alignment or a prediction. Missing Corporate evidence remains explicit and
does not become neutral evidence.

The existing institutional, fundamental and cross-layer contracts remain
separate and their source ownership is unchanged.
