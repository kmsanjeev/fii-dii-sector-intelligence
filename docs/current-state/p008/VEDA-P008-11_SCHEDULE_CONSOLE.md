# VEDA-P008 Schedule Console

Date: `2026-08-11`

P008 provides schedule visibility and safe editing without turning on continuous orchestration.

## Exposed Schedule Fields

- mission
- cadence
- timezone
- enabled
- last run
- next run
- overlap policy
- misfire policy

## Supported Admin Changes

- enable/disable
- cadence type
- overlap policy
- misfire policy

## Boundary

P008 does not activate hourly/daily/weekly continuous loops by itself. It only exposes the schedule records and safe mutations already supported by the research platform.

