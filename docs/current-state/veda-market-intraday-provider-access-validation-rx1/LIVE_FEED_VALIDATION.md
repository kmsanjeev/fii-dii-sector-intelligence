# Live feed validation

The validation date was Saturday, 22 August 2026, outside regular NSE market
hours, and the account Data API plan was inactive. No WebSocket was started,
no background service was left running, and no live tick was fabricated.

State: `LIVE_SESSION_VALIDATION_PENDING`.

The next access validation may test authentication, minimal subscribe,
heartbeat, unsubscribe and clean disconnect after entitlement is active.
