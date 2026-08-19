# Configuration API

- `GET /api/chat/capabilities` — public capability discovery plus policy state.
- `GET /api/veda/configuration` — admin-only full configuration.
- `PUT /api/veda/configuration/access/{capability_id}` — admin-only access update.
- `POST /api/veda/configuration/reset` — admin-only full available defaults.

Write operations use existing `require_admin` authentication. No secrets are
returned or accepted. Research access and provider availability are separate.
