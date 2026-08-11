# VEDA-P008 Notification Model

Date: `2026-08-11`

P008 adds in-app research attention cards and notification rows without introducing external delivery channels.

## Current Notification Kinds

- new high-priority candidate
- contradiction detected
- candidate enriched with additional evidence
- high-stakes candidate
- failed run
- repeatedly failing mission

## Deduplication

Notification rows are deduplicated in the service layer before the UI renders them.

## Boundary

- in-app notifications: `YES`
- email/telegram/push: `NOT IMPLEMENTED IN P008`

