# Capability Architecture

The capability registry is machine-readable and links every future Jyotisha capability to:

- required runtime facts from P012
- approved-core claims and rules from P010/P011
- lifecycle gates
- validation/shadow/activation policy

| Capability ID | Name | Status | Domain | Subdomain | Safety |
| --- | --- | --- | --- | --- | --- |
| `VEDA-CAP-FOUNDATION-000001` | D1 canonical chart calculation | ACTIVE | FOUNDATION | D1 | LOW |
| `VEDA-CAP-FOUNDATION-000002` | Canonical graha and lagna chart facts | ACTIVE | FOUNDATION | GRAHA_LAGNA_FACTS | LOW |
| `VEDA-CAP-TIMING-000001` | Vimshottari runtime baseline | ACTIVE | TIMING | VIMSHOTTARI | LOW |
| `VEDA-CAP-DIGNITY-000001` | Graha dignity governed rule migration | ACTIVATION_READY | STRENGTH | DIGNITY | LOW |
| `VEDA-CAP-INTERPRETATION-000001` | Graha and bhava interpretive rules | RESEARCHING | FOUNDATION | GRAHA_BHAVA_INTERPRETATION | MODERATE |
| `VEDA-CAP-VARGA-000001` | Navamsha (D9) calculation | IDENTIFIED | DIVISIONAL_CHARTS | D9 | MODERATE |
| `VEDA-CAP-VARGA-000002` | Navamsha (D9) interpretation | IDENTIFIED | DIVISIONAL_CHARTS | D9_INTERPRETATION | MODERATE |
| `VEDA-CAP-VARGA-000003` | Dashamsha (D10) calculation | IDENTIFIED | DIVISIONAL_CHARTS | D10 | MODERATE |
| `VEDA-CAP-VARGA-000004` | Dashamsha (D10) interpretation | IDENTIFIED | DIVISIONAL_CHARTS | D10_INTERPRETATION | MODERATE |
| `VEDA-CAP-RULE-000001` | Yoga governed detection framework | RESEARCHING | RULE_SYSTEMS | YOGA | MODERATE |
| `VEDA-CAP-RULE-000002` | Dosha governed detection framework | RESEARCHING | RULE_SYSTEMS | DOSHA | HIGH |
| `VEDA-CAP-TIMING-000002` | Yogini Dasha expansion | IDENTIFIED | TIMING | YOGINI_DASHA | MODERATE |
| `VEDA-CAP-TIMING-000003` | Ashtottari Dasha expansion | IDENTIFIED | TIMING | ASHTOTTARI_DASHA | MODERATE |
| `VEDA-CAP-TIMING-000004` | Transit / gochar structural comparison | IDENTIFIED | TIMING | GOCHAR | MODERATE |
| `VEDA-CAP-STRENGTH-000001` | Shadbala governed strength system | IDENTIFIED | STRENGTH | SHADBALA | MODERATE |
| `VEDA-CAP-STRENGTH-000002` | Ashtakavarga governed strength system | IDENTIFIED | STRENGTH | ASHTAKAVARGA | MODERATE |
| `VEDA-CAP-DOMAIN-000001` | Marriage intelligence | RESEARCHING | LIFE_DOMAINS | MARRIAGE | MODERATE |
| `VEDA-CAP-DOMAIN-000002` | Career and education intelligence | RESEARCHING | LIFE_DOMAINS | CAREER | MODERATE |
| `VEDA-CAP-DOMAIN-000003` | Finance intelligence | RESEARCHING | LIFE_DOMAINS | FINANCE | HIGH_STAKES |
| `VEDA-CAP-DOMAIN-000004` | Children and family intelligence | RESEARCHING | LIFE_DOMAINS | CHILDREN | MODERATE |
| `VEDA-CAP-DOMAIN-000005` | Health intelligence | RESEARCHING | LIFE_DOMAINS | HEALTH | HIGH_STAKES |
| `VEDA-CAP-DOMAIN-000006` | Longevity intelligence | RESEARCHING | ADVANCED | AYURDAYA | HIGH_STAKES |
| `VEDA-CAP-DOMAIN-000007` | Remedy governance | RESEARCHING | ADVANCED | REMEDIES | HIGH_STAKES |
| `VEDA-CAP-ADVANCED-000001` | Jaimini systems | IDENTIFIED | ADVANCED | JAIMINI | MODERATE |
| `VEDA-CAP-ADVANCED-000002` | Muhurta and electional astrology | IMPLEMENTING | ADVANCED | MUHURTA | MODERATE |
