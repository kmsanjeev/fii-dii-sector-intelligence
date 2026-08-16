# Privacy and Data Lifecycle

| Stage | Data/store | Access and controls | Deletion/backup rule |
|---|---|---|---|
| Registration | contact metadata / separate identity vault | identity steward only; encrypted | delete or sever linkage on withdrawal |
| Consent | versioned scopes and notice evidence / consent store | participant and reviewer; append-only audit | preserve minimum audit evidence subject to counsel |
| Identity | minimum linkage / separate vault | separate principal, key and audit boundary | delete or sever linkage |
| Birth document | original only if approved, otherwise verification metadata and fingerprint | isolated encrypted store; allowlist, signature and malware checks | prefer no-original retention; backup tombstone required |
| Verification | tier, precision, conflict, source hash / research store | evidence adjudicator | retain per approved study schedule |
| Event follow-up | category, precision and provenance / research store | consent-scoped reviewer access | stop future use on withdrawal |
| Snapshot | hashes and eligibility / snapshot registry | lock and audit | immutable treatment requires counsel review |
| Export | restricted deidentified extract / export boundary | approval, encryption and export log | no direct identifiers, vault keys, documents or uncontrolled free text |
| Retention | approved metadata and permitted outputs | research admin | provisional until legal review |
| Withdrawal | status, deletion proof, tombstone / all relevant stores | research admin and auditor | verify primary and backup handling |

The recommended minimum-retention option is verification metadata plus a
cryptographic fingerprint, with originals retained only when an approved
protocol, counsel and security review justify it.
