# External Provider Registry

P009 extends the provider contract with two external-capable providers:

- `ddgs-search`
  - type: `WEB_SEARCH`
  - purpose: discovery/query execution
  - status: disabled by default unless `VEDA_RESEARCH_EXTERNAL_ENABLED=true` and `VEDA_RESEARCH_EXTERNAL_SEARCH_ENABLED=true`

- `requests-fetch`
  - type: `DIRECT_WEB`
  - purpose: safe retrieval and lightweight extraction
  - status: disabled by default unless `VEDA_RESEARCH_EXTERNAL_ENABLED=true` and `VEDA_RESEARCH_EXTERNAL_RETRIEVAL_ENABLED=true`

Runtime provider state tracks:
- status
- enabled
- cooldown
- last success
- last failure
- consecutive failures

Search ranking is treated as discovery only. Source authority still comes from domain governance, not provider rank.
