# Prospective Pilot

`make_prospective()` explicitly marks a record `PROSPECTIVE_CASE` and clears outcome fields. The durable registry locks records by default and preserves prediction timestamps, method versions, cutoffs, and evidence. No future outcome is invented. Genuine user/chart cases can be issued later and resolved through the existing outcome workflow.
