# Full Suite and Frontend Report

Final full Python command: `py -3.11 -m pytest -q`.

Result: `1,285 passed, 1 warning in 611.14s (0:10:11)`.

The first final-tree run reached `1,284 passed` and exposed the stale API
contract snapshot. The canonical fixture was regenerated with
`scripts/generate_p001_api_baseline.py`, its endpoint assertions were updated
from 142/155 to 145/158, and the full suite was rerun to the result above.

Frontend: `npm test -- --run src/test` passed (`8 files, 29 tests`); `npm run
build` passed with the existing Vite large-chunk warning. Full test discovery
outside `src/test` is conditionally blocked only by the ignored local
`node_modules.pre-npm-ci-*` backup directory, not by application tests.
