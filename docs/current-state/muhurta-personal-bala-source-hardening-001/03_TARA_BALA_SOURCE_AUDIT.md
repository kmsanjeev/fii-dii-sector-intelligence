# Tara Bala source audit

## Finding

The operational candidate is the Navatara calculation: count inclusively from
Janma Nakshatra to event Nakshatra across the 27-star cycle, then map the
remainder modulo nine to nine named Tara categories. This is repeated by modern
implementation witnesses and is suitable for a diagnostic oracle.

It is **not** promoted to `VALIDATED_KNOWLEDGE`: the accessible 1902
Muhurtacintamani scan is public-domain metadata plus partial/OCR text, and the
relevant primary passage could not be verified with stable chapter/verse/page
provenance. Search snippets and modern pages were used only for variant discovery.

## Candidate calculation

`count = ((event_nakshatra - janma_nakshatra) mod 27) + 1`; `remainder = count mod 9`.
Remainders 1..8 and 0 map to Janma, Sampat, Vipat, Kshema, Pratyari, Sadhaka,
Naidhana, Mitra and Parama Mitra respectively.

## Advisory governance

The diagnostic table uses `SUPPORTIVE` for Sampat/Kshema/Sadhaka/Mitra/Parama
Mitra and `CAUTION` for Janma/Vipat/Pratyari/Naidhana. These are not hard
exclusions and remain `SOURCE_SEMANTICS_PARTIAL`. Name variants such as Vadha
for Naidhana, Pratyak/Pratyara for Pratyari, and Ati-Mitra for Parama Mitra are
preserved as variants rather than merged silently.

## Decision

`TARA_BALA_SOURCE_PARTIAL`; no production evaluator or API activation.
