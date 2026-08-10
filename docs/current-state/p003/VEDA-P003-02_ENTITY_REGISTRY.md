# VEDA-P003-02 Entity Registry

## Registry Counts

| Registry | Count |
| --- | ---: |
| Grahas | 12 |
| Rashis | 12 |
| Bhavas | 12 |
| Nakshatras | 27 |
| Vargas | 16 |
| Dashas / Timing | 6 |
| Relationship Concepts | 9 |
| Dignities | 8 |
| House Classifications | 9 |
| Domains | 10 |
| Yogas | 10 |
| Total Entities | 131 |

## Files

- `data/veda/ontology/grahas/grahas.json`
- `data/veda/ontology/rashis/rashis.json`
- `data/veda/ontology/bhavas/bhavas.json`
- `data/veda/ontology/nakshatras/nakshatras.json`
- `data/veda/ontology/vargas/vargas.json`
- `data/veda/ontology/dashas/dashas.json`
- `data/veda/ontology/relationships/relationships.json`
- `data/veda/ontology/dignities/dignities.json`
- `data/veda/ontology/house_classifications/house_classifications.json`
- `data/veda/ontology/domains/domains.json`
- `data/veda/ontology/yogas/yogas.json`

## Relation Registry

`data/veda/ontology/relations/core_relations.json` currently provides `34` graph-compatible relations, including:

- graha -> rules -> rashi
- bhava -> belongs_to_domain -> domain
- varga -> specializes -> domain
- dasha sublevels -> part_of -> Vimshottari
- Vimshottari sequence graha ordering

## Intentional Scope

This registry is a canonical vocabulary layer, not a runtime-capability claim.

Example:

- `VEDA-VARGA-D24` exists in ontology because VEDA needs a stable term for future research and rules
- that does not imply the current runtime calculates or interprets D24
