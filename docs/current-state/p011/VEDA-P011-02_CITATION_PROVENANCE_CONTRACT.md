# Citation Provenance Contract

Approved-core retrieval now carries structured citation objects with:
- `source_id`
- `passage_id`
- `claim_id`
- `rule_id`
- `work`
- `author`
- `chapter`
- `section`
- `verse`
- `page`
- `edition`
- `translator`
- `publisher`
- `source_uri`
- `verification_status`
- `retrieved_at`

Citation sources are drawn from governed P002/P010 artifacts only. The chat layer is explicitly instructed not to fabricate missing chapter, verse, page, author, or source details.
