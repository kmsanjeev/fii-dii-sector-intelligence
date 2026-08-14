# VEDA-HUMAN-EVAL-001

## Founder Blind Response & Group-Intelligence Evaluation

Status: `FOUNDER_RATINGS_REQUIRED`

This package evaluates the technically validated COMM-002 and GROUP-001
implementations. It does not change production behavior and does not claim
human validation before the Founder submits ratings.

## Integrity Rules

- Keep the response-generation variables constant: model, provider settings,
  knowledge context, chart facts, user input, and safety state.
- Generate one baseline/default response and one adaptive/group-aware response
  for each case using an approved controlled process.
- Randomize A/B assignment per case and store the mapping separately from this
  Founder-facing document. Do not reveal it before ratings are complete.
- Do not use this evaluation to tune COMM-002, GROUP-001, or LANG-001.
- Do not fabricate response text, ratings, comments, or preference counts.
- Save completed ratings only after the Founder has finished all cases.

## Current Runtime Finding

The repository has no baseline/adaptive runtime switch and no suitable existing
evaluation UI or result store. The current ChatEngine applies its adaptive
guidance through the normal response path. Therefore this package is ready for
Founder evaluation, but response pairs must first be captured by a controlled
evaluation runner that can produce both configurations without changing
production architecture. Blank response slots below are intentional.

## COMM-002: 10 Blind A/B Cases

For each case, insert the two captured responses without exposing their mode.
The evaluator sees only `Response A` and `Response B`.

### Case 1 - Small Talk

User prompt: `I finally have a quiet weekend. Any simple ideas for making it feel good?`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 2 - Heart-to-Heart

User prompt: `I have people around me, but lately I still feel very alone. I do not know how to talk about it.`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 3 - Straight Talk

User prompt: `Give me a straight answer: should I change this plan or keep going?`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 4 - Jyotisha Beginner

User prompt: `What is D9 in a birth chart? Please explain it simply.`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 5 - Jyotisha Expert

User prompt: `The D9 lord is afflicted, but MD/AD activation looks weak. How should I weigh those signals?`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 6 - Software Beginner

User prompt: `What is a race condition? Explain it without assuming I am a programmer.`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 7 - Software Expert

User prompt: `We need an idempotent migration, but the deploy can overlap with an older worker. What risks should I review?`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 8 - Hinglish

User prompt: `Yaar, scene kya hai? Seedha batao, ye plan kaam karega ya nahi?`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 9 - High-Stakes Caution

User prompt: `I have recurring headaches and fatigue. Can astrology tell me whether this is serious?`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### Case 10 - Finance Shop Talk

User prompt: `Compare these two strategies using drawdown, liquidity, and risk-on versus risk-off behavior.`

Response A: `[RESPONSE_CAPTURE_REQUIRED]`

Response B: `[RESPONSE_CAPTURE_REQUIRED]`

### COMM-002 Rating Form

Rate each response from 1 to 5, then select a preference. Add a comment only if useful.

| Case | Metric | A | B |
|---|---|---:|---:|
| 1-10 | Precision |  |  |
| 1-10 | Relevance |  |  |
| 1-10 | Naturalness |  |  |
| 1-10 | Depth |  |  |
| 1-10 | Clarity |  |  |
| 1-10 | Tone appropriateness |  |  |
| 1-10 | Non-repetition |  |  |
| 1-10 | Confidence quality |  |  |
| 1-10 | Overall usefulness |  |  |

Where relevant, also rate Chart Specificity and Timing Usefulness. For each
case record: `Preferred: A / B / TIE`, `Surprisingly useful insight: A / B /
BOTH / NEITHER`, and an optional comment.

## GROUP-001: 7 Scenarios

Capture one group-aware response for each transcript. Display only participant
labels and the response; keep expected state in the evaluator's private record.

1. `RAVI`: asks about his daughter's chart. `VEDA`: responds while keeping
   speaker, chart subject, and addressee separate.
2. Two astrologers disagree about D9 timing; VEDA provides a neutral synthesis.
3. Three participants debate portfolio allocation and change positions.
4. A Hinglish exchange contains disagreement and one participant explicitly
   addresses VEDA.
5. The group explicitly asks VEDA to summarize competing positions.
6. Conflict rises between participants, then one apologizes and the exchange
   de-escalates.
7. One participant asks another a question while VEDA is not addressed and
   should normally observe.

For each scenario, capture the transcript and response pair/result under the
same blinded protocol. Rate every applicable response 1-5 for:

- Speaker Attribution
- Reply-To Understanding
- Addressee Understanding
- Topic Understanding
- Viewpoint Attribution
- Neutrality
- Group Understanding
- Non-Interruption / Participation Judgment
- Response Relevance
- Naturalness
- Overall Usefulness

Also record optional comments and any critical failure: `WRONG_SPEAKER`,
`WRONG_ADDRESSEE`, `WRONG_CHART_SUBJECT`, `FABRICATED_VIEWPOINT`,
`HOSTILE_ESCALATION`, or `INAPPROPRIATE_TONE`.

## Private Evaluation State

Do not place the A/B mapping in this Founder-facing file. Keep it in a private,
access-controlled evaluator artifact until all ratings are submitted. Use
`results-template.json` for the blank result shape; it contains no ratings and
no mapping.

## Completion

The Founder must complete all available response pairs and ratings, save the
completed result artifact, and return it for calculation. Until then:

- COMM-002 technical status: `IMPLEMENTED / FROZEN`; human status: `PENDING`.
- GROUP-001 technical status: `IMPLEMENTED / FROZEN`; human status: `PENDING`.
- EMP-001 remains independent and unchanged.
