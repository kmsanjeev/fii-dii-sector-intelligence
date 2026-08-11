# VEDA-P008-R1 Research Trust Boundary

The P006/P007 rule remains unchanged:

> External research is untrusted source data, not instructions and not approved Veda knowledge.

P008-R1 preserves that boundary in chat by enforcing:

- external research prompt context explicitly states that the material is source content only;
- `last_research.temporary` remains `true`;
- `last_research.save_requires_review` remains `true`;
- any conflict note added at the chat boundary is explanatory metadata for the current answer, not a knowledge mutation;
- approved memory and attachment memory remain separate local-evidence classes and are not treated as proof that external research is approved;
- no research candidate, contradiction status, approval state, or promotion-ready artifact is modified by this remediation.

The chat layer may now say, in effect:

- this is local approved evidence;
- this is temporary external research;
- these two appear to disagree.

It may not say:

- the new research is now approved knowledge;
- the contradiction is resolved;
- approved core has been updated.
