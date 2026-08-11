# VEDA-P008-R1 Dependency Baseline

## Findings

On August 11, 2026, the full validation suite required:

- `pyswisseph`
- `requests`
- `jsonschema`

Manifest status before reconciliation:

- `pyswisseph`: already declared in `requirements.txt`
- `requests`: already declared in `requirements.txt`
- `jsonschema`: **missing** from `requirements.txt` even though committed tests imported it

P008-R1 corrected that gap by adding:

```text
jsonschema>=4.23.0
```

to `requirements.txt`.

## Reproducible Preparation Process

Python:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

Validation entry points used in this phase:

```powershell
py -3.11 -m pytest -q
py -3.11 scripts/validate_p002_astrology_registry.py
py -3.11 scripts/validate_p003_astrology_ontology.py
py -3.11 scripts/validate_p004_calculation_foundation.py
py -3.11 scripts/validate_p005_interpretation_validation.py
py -3.11 scripts/validate_p006_research_platform.py
cmd /c npx vitest run --pool=threads --maxWorkers=1
cmd /c npm run build
```

Runtime smoke:

```powershell
py -3.11 scripts/run_p001_smoke.py
```

Known condition:

- the official smoke command still hits the inherited Windows temporary-directory cleanup defect after the checks complete;
- `run_smoke()` itself returned `PASS` when invoked with cleanup errors suppressed at call time for validation-only purposes.
