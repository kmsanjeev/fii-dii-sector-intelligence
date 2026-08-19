# Full-suite observations

The first full command was:

```text
py -3.11 -m pytest -q --durations=25 --durations-min=0.1
```

It exceeded 900 seconds and stopped at approximately 95%. The captured tail
showed `tests/test_veda_std_001.py::test_document_learning_compares_before_candidate_creation`
loading the `sentence-transformers/all-MiniLM-L6-v2` model through Hugging
Face and FAISS. The isolated test passed in 26.21s, so the evidence is a
network/model-initialization dependency rather than a deadlock in that test.

After the bounded inventory-scope remediation, the same authoritative command
completed:

```text
1266 passed, 1 warning in 618.56s (0:10:18)
```

The quiet diagnostic variant (`-o log_cli=false -o log_file=`) completed with
`1266 passed` in `595.02s`; logging is therefore a minor contributor, not the
root cause and global logging semantics were preserved.

The final authoritative run after adding the three infrastructure tests was:

```text
1269 passed, 1 warning in 594.91s (0:09:54)
```
