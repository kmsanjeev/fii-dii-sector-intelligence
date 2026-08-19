# Godhuli Source Audit

{
  "factor_id": "MUHURTA_GODHULI_INTERVAL",
  "source_witnesses": [
    {
      "assertion_id": "VEDA-SWW-ASSERTION-BS-MARRIAGE-GODHULI-001",
      "work": "Brihat Samhita",
      "chapter": "103",
      "passage": "verse 13, consulted translation",
      "url": "https://www.wisdomlib.org/hinduism/book/brihat-samhita/d/doc229367.html",
      "claim": "Godhuli is presented as a distinct marriage context in which ordinary Nakshatra/Tithi/Yoga/Karana/Lagna considerations need not be applied in that context.",
      "authority": "CLASSICAL_PRIMARY_SCOPED_TRANSLATION_WITNESS"
    },
    {
      "assertion_id": "VEDA-SWW-ASSERTION-MC-MARRIAGE-BALA-LAGNA-001",
      "work": "Muhurtacintamani",
      "edition": "1945 digitized edition by Narayanram Acharya",
      "passage": "marriage section, digitized page 249",
      "url": "https://jainqq.org/explore/002342/249",
      "claim": "Marriage context discusses Guru/Sun/Moon strength and marriage Lagna context; it does not provide a universally normalized civil-time Godhuli interval here.",
      "authority": "TRADITIONAL_EDITION_WITNESS"
    }
  ],
  "definition": "Contextual traditional twilight/cow-dust term; exact interval semantics are not sufficiently resolved for a universal machine factor.",
  "instant_or_interval": "UNRESOLVED; do not collapse to sunset timestamp",
  "sunset_dependency": "Existing MUHURTA_FOUNDATION_SOLAR_DAY_NOAA_APPROX_V1 sunset fact is reusable as a solar dependency only.",
  "source_semantics": "SOURCE_PARTIAL",
  "variants": [
    "contextual marriage exception",
    "later/local twilight conventions",
    "unresolved duration and solar-altitude rule"
  ],
  "high_latitude_policy": "UNAVAILABLE_IF_SUNSET_UNAVAILABLE; never fabricate",
  "advisory_effect": "ACTIVITY_CONTRACT_ONLY; not embedded in factor",
  "state": "GODHULI_CALCULATION_READY_SOURCE_PARTIAL"
}
