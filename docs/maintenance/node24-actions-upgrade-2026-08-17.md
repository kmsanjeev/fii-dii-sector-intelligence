# Node.js 24 GitHub Actions Runtime Upgrade

Date: 2026-08-17

## Scope

This change upgrades only the Node.js runtime used internally by GitHub Actions:

- `actions/checkout@v4` → `actions/checkout@v5`
- `actions/setup-python@v5` → `actions/setup-python@v6`

The application Python runtime remains `3.11.9`. No system Node installation,
frontend dependency, Python dependency, generated data, or production engine
code is changed.

## Before checkpoint

- Branch: `main`
- Commit: `8f5a61e8a57917ada0e09f74efe9b3bc118a5a44`
- Workflow: `.github/workflows/daily.yml`
- Local Node: `v24.16.0`
- Local npm: `11.13.0`
- Existing unrelated untracked file: `data/pipeline.stop` (preserved)

## Validation plan

1. Confirm only the workflow and this record are staged.
2. Validate action references and workflow syntax.
3. Confirm Python version remains `3.11.9`.
4. Run frontend dependency/build checks where the local environment permits.
5. Commit and push selectively.
6. Verify the final tree and record the rollback commit.

## Rollback

To revert this upgrade after the commit is identified, run:

```powershell
git revert <upgrade-commit>
git push origin main
```

The manual equivalent is to change `checkout@v5` back to `checkout@v4` and
`setup-python@v6` back to `setup-python@v5`, then commit only that workflow
reversion. Do not reset or force-push the branch.
