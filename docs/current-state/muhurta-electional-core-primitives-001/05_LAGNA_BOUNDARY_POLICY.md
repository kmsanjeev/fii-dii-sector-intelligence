# Lagna Boundary Policy

{
  "policy_id": "MUHURTA_LAGNA_BOUNDARY_POLICY_V1",
  "boundary_set": "0,30,60,...,330 degrees sidereal",
  "normal_interval": "[start,end)",
  "uncertainty": "If the governed/reference comparison can cross a sign boundary, emit BOUNDARY_AMBIGUOUS.",
  "no_silent_choice": true,
  "no_houses_ex_migration": true,
  "downstream": "Any activity predicate requiring a sign must abstain; a non-sign-dependent fact may remain available.",
  "hash": "D600A0C44A3CCC63BD018379DBF212F17ACD5773EFEAFAB9D1F2128F9ACFBBF4"
}
