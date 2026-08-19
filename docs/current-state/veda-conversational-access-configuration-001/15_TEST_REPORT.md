# Focused Validation

Final focused validation: `38 passed, 1 warning` across the canonical API
contract snapshot, new access-configuration tests, existing chat
router/engine tests, and STD-003 conversation tests. The updated STD-003
assertion intentionally verifies that general emotional conversation does not
invoke market retrieval. The warning is the existing Starlette/httpx
deprecation warning.

Frontend source tests: `8 files, 29 tests passed`. Production build passed;
Vite emitted only the existing large-chunk warning. The broad `npm test --
--run` discovery command remains noisy in this local workspace because an
ignored `node_modules.pre-npm-ci-*` backup is scanned as a test tree; the
source-test command above is the deterministic release check.
