# Continuous Research Pilot

P009 does not enable uncontrolled broad crawling.

The implemented pilot scope is controlled and test-driven:
- hourly execution
- daily execution
- weekly execution
- candidate enrichment over repeated cycles
- provider fallback and cooldown
- unsafe-source rejection
- runtime independence from the Admin UI

External providers are implemented but remain disabled by default pending explicit environment configuration and live validation.
