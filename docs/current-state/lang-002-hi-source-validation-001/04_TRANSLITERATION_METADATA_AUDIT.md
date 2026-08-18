# Transliteration Metadata Audit

The existing registry values `Surya`, `Chandra`, `Mangala`, `Budha`, `Guru`,
`Shukra`, `Shani`, `Rahu`, and `Ketu` are retained for compatibility with
existing searches. They are not silently relabelled as strict IAST.

For the nine graha entries, a separate `iast` field and explicit metadata roles
were added:

| Canonical ID | Retained legacy Roman | IAST | Metadata result |
|---|---|---|---|
| `TERM.PLANET.SUN` | Surya | Sūrya | legacy retained; IAST separate |
| `TERM.PLANET.MOON` | Chandra | Candra | legacy retained; IAST separate |
| `TERM.PLANET.MARS` | Mangala | Maṅgala | legacy retained; IAST separate |
| `TERM.PLANET.MERCURY` | Budha | Budha | legacy retained; IAST separate |
| `TERM.PLANET.JUPITER` | Guru | Guru | legacy retained; IAST separate |
| `TERM.PLANET.VENUS` | Shukra | Śukra | legacy retained; IAST separate |
| `TERM.PLANET.SATURN` | Shani | Śani | legacy retained; IAST separate |
| `TERM.PLANET.RAHU` | Rahu | Rāhu | legacy retained; IAST separate |
| `TERM.PLANET.KETU` | Ketu | Ketu | legacy retained; IAST separate |

The IAST/Indic transliteration distinction is governed by the ISO 15919
reference recorded in `01_EXTERNAL_REFERENCE_REGISTER.md`. No IAST values were
invented for signs, Vargas, Dashas, or Panchanga terms because the existing
registry does not carry source-reviewed Sanskrit spellings for those fields.
All existing aliases remain available.
