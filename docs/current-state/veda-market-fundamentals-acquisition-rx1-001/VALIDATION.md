# Validation record

Focused provider and downstream contract tests: `17 passed`.

Targeted Ruff (`I,DTZ,RUF`): passed for changed code and tests.

Python compilation: passed.

Controlled live acquisition:

- command: `py -3.11 engines/fundamentals/financial_results_engine.py --windows 2`
- official master windows queried: `Q4FY26`, `Q3FY26`
- source master requests: `2`
- XBRL record fetches: `8`
- normalized result: `32403` rows / `2333` symbols
- new normalized records on first run: `8`
- new reporting periods: `0`
- duplicate canonical keys after run: `0`
- second-run hash stable: yes
- second-run modification time stable: yes

Full FII suite: `1335 passed, 1 warning` in `681.58s`.

Full VEDA platform suite: exited `0`, warnings only. The warnings are existing
Authlib/Starlette dependency deprecations and optional model/network notices;
they are not test failures.
