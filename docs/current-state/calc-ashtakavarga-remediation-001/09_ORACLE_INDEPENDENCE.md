# Oracle Independence

The diagnostic is independent of `engines.ai.knowledge.shadbala_engine`. It
reads only the frozen contract and source-matrix artifacts, recomputes the
matrix hash and aggregates the source bindu cells directly.

The canonical production oracle comparison was not started because the
contract consistency gate failed first. This prevents circular validation and
prevents a production table from becoming its own expected-output generator.
