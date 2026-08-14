# LANG-001-R1 Baseline

Starting commit: `f511bbd5f2df697d1071c5a01a856fbea2ae9b00`.

The frozen LANG-001 benchmark fingerprint was `c3a7159e361f601fa8daf612a9df9c66b436832ef781c2f2df24574cb90dac66`.
It contained 100 cases: 90 known and 10 unknown. The published baseline was
54/90 known resolution labels (60%) and 0/10 fabricated unknown definitions.

The original 36-case failure inventory was reproduced before remediation:
English 17, Hindi 13, Hinglish 6.

Nine fixture metadata defects were isolated rather than hidden: HI13, HI14,
HI19, HI20, HG17, HG18, HG19 were exact governed phrase entries incorrectly
labelled NONE, HG20 was the same issue, and M09 used a Devanagari `contains`
value for a Roman-Hindi input. These corrections are recorded separately from
resolver gains; the original published score remains 54/90.
