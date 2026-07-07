# Contributing

Thanks for your interest in improving `ai-smoketest`. This document covers the local dev loop, coding conventions, and PR expectations.

## Dev environment

The fastest path is the bundled devcontainer:

1. Clone the repo and open it in VS Code.
2. When prompted, **Reopen in Container**. The devcontainer provides Python 3.12, the Azure CLI, `actionlint`, `ruff`, and `pytest`.
3. Verify:
   ```bash
   python3 --version
   actionlint --version
   ruff --version
   pytest --version
   ```

If you'd rather run outside a container, install those four tools on your host.

## Running the runner locally

The runner is stdlib-only Python. To smoke-test a live agent from your workstation:

```bash
az login
python3 scripts/smoke-tests.py \
  --project-endpoint https://<acct>.services.ai.azure.com/api/projects/<proj> \
  --agent-name <your-agent> \
  --tests-file examples/smoke-tests.json
```

A clean run prints `Summary: N/N passed across 1 agent(s)` and exits `0`.

## Running the tests

```bash
pytest tests/ -q
```

Unit tests cover the pure functions (`extract_text`, `check_assertions`, `_ascii_fold`) — no network required.

## Linting

```bash
actionlint          # action.yml + .github/workflows/*.yml
ruff check scripts/ tests/
```

Both must exit `0` for CI to pass.

## Making a change

1. Open an issue first for anything that changes the action's input/output surface or the catalog schema. Small bug fixes can go straight to a PR.
2. Update `README.md` when you add or rename an input — the `readme-inputs-sync` CI job will fail otherwise.
3. Update `examples/smoke-tests.json` when you add a new catalog field.
4. If your change affects the runner's HTTP contract with the Foundry data plane, exercise it end-to-end against a live agent and paste the `Summary:` line into the PR description.

## Semver impact

| Change | Version bump |
|---|---|
| Drop or rename an input | major |
| Add an input, add a catalog field, add a new assertion type | minor |
| Runner bug fix, docs, dependency bump | patch |

## PR checklist

- [ ] `actionlint` passes.
- [ ] `ruff check scripts/ tests/` passes.
- [ ] `pytest tests/ -q` passes.
- [ ] `README.md` inputs table matches `action.yml`.
- [ ] For runner behaviour changes: tested end-to-end against a live Foundry agent.
- [ ] Correct semver label applied.
