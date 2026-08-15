# Architecture

The foundation is implemented in
`engines/ai/knowledge/muhurta_foundation.py` and is deliberately separate from
ChatEngine and the birth-chart Panchanga formatter.

Flow:

`MuhurtaRequest -> validation -> solar-day facts -> explicit dependency gates`

The module has no provider calls, no persistence, no RAG integration and no
recommendation path. The capability registry records the capability as
`IMPLEMENTING` with activation still `INACTIVE` and validation limited to the
foundation.
