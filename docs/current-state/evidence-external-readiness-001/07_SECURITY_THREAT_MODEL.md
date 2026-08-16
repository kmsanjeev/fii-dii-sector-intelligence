# Security Threat Model

| Threat | Impact | Likelihood | Current control | Gap/remediation | Recruitment blocking |
|---|---|---|---|---|---|
| Enumeration / IDOR | High | Medium | no endpoint | deny-by-default IDs, object authorization and rate limits | YES |
| Identity/research relinking | High | Medium | logical separation design | deploy separate vault, principal and key boundary | YES |
| Birth-document leakage | High | Medium | no real documents | encrypted isolated store, allowlist, signature validation, AV/CDR | YES |
| Export reidentification | High | Medium | synthetic deidentified export | field minimization and reidentification review | YES |
| Audit/secret leakage | High | Low–Medium | design only | redaction, secret manager, access review | YES |
| Backup exposure/deletion failure | High | Medium | design only | encrypted backups, tombstones and deletion verification | YES |
| Admin compromise/insider access | High | Medium | roles documented | strong auth, dual control and periodic review | YES |
| Malicious upload/metadata | High | Medium | no upload endpoint | OWASP controls and sandbox/scanning | YES |
| Consent tampering | High | Low | versioned design | append-only signed consent events | YES |
| Prospective-ledger tampering | High | Low | interface documented | lock method/hash/timestamp and separate outcomes | YES |
| Cross-environment leakage | High | Medium | no production collection | separate accounts, credentials, datasets and CI checks | YES |

No penetration test, security certification or incident deadline claim was made.
