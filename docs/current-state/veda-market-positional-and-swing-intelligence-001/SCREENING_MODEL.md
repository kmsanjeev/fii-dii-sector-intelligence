# Screening model

Screening first performs a cheap technical prefilter, then deep-analyzes a
bounded candidate set (`max(limit*3, 20)` with a hard request limit of 50).
The response exposes the universe, prefilter and deep-analysis counts. It does
not call every symbol's full Theme/F&O stack and has no N+1 over the complete
technical universe.
