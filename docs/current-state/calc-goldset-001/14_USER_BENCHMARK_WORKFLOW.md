# User DOB/TOB/POB Benchmark Workflow

The script accepts an optional CSV or JSON input through `--user-benchmark`. Required fields are `case_id`, `dob`, `tob`, `place`, `time_precision`, `birth_source`, and `documentary_status`. Accepted birth-source values are validated explicitly. Invalid records are reported rather than silently normalized.

The pathway is calculation-only. Life events are not required, no user record is automatically classified as GOLD, no personal data is committed by this activity, and the workflow does not activate production or predictive use.

