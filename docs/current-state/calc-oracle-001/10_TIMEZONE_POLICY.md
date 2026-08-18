# Timezone policy and regression

Civil-time resolution is explicit: documentary fixed offset first, then an IANA historical zone, then unresolved. A nonexistent local civil time is not silently converted, and an overlap is not silently assigned one fold.

The seven-case regression covers India, a New York DST gap, a New York DST fold, historical Berlin, Lord Howe half-hour time, Nepal quarter-hour time, and the Kiritimati date line. Results: 5 unambiguous resolved cases, 1 explicit ambiguous fold, and 1 explicit unresolved gap. All seven are correctly classified; no false precision is introduced.

