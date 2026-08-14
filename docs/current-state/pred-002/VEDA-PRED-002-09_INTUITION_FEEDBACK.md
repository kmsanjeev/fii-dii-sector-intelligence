# Intuition Feedback

Combination feedback is conservative and versioned. `combination_recommendation()` returns `INSUFFICIENT_SAMPLE` below a recurrence threshold, then `RETAIN`, `CONTEXT_DEPENDENT`, or `DECREASE_RELATIVE_IMPORTANCE` based on observed results. Recommendations do not mutate authoritative weights; future weighting remains experimental and reversible.
