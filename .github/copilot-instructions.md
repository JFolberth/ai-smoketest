# ai-smoketest — Copilot Instructions

A GitHub Marketplace Action that smoke-tests Microsoft Foundry hosted agents by POSTing prompts from a JSON catalog to the Responses data-plane endpoint and asserting on the reply text. Composite action + bundled stdlib-only Python runner.

---

## Architecture

| Layer | What it is |
|---|---|
| [action.yml](../action.yml) | Composite `action.yml` at repo root (Marketplace requires root location). Declares 4 inputs and one bash step that fans out comma-separated `agent_name` into repeated `--agent-name` flags, then invokes the bundled runner via `${GITHUB_ACTION_PATH}/scripts/smoke-tests.py`. |
| [scripts/smoke-tests.py](../scripts/smoke-tests.py) | The runner. Pure Python 3.12 stdlib. POSTs to `{project_endpoint}/agents/{agent_name}/endpoint/protocols/openai/responses?api-version=2025-11-15-preview`. Assertion matchers: `contains_any`, `contains_all`, `contains_none` (case-insensitive substring, smart-quote folded). Threading via `previous_response_id` or `conversation` id. |
| [examples/smoke-tests.json](../examples/smoke-tests.json) | Copy-paste catalog template (2 tests: single-turn + threaded). Not an implicit default — `tests_file` input is required. |
| [examples/workflow.yml](../examples/workflow.yml) | Copy-paste sample workflow showing `actions/checkout@v7` → `azure/login@v3` (OIDC) → this action. |
| [tests/test_smoke_tests.py](../tests/test_smoke_tests.py) | Pure-function unit tests for `extract_text`, `check_assertions`, `_ascii_fold`. No network. |
| [tests/check_readme_inputs.py](../tests/check_readme_inputs.py) | CI guard: every `action.yml` input must appear backtick-wrapped in `README.md`. Runs in the `readme-inputs-sync` job. |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | 4 jobs: `lint-action` (actionlint + yamllint), `lint-python` (ruff + compileall), `unit-tests` (pytest), `readme-inputs-sync`. |
| [.devcontainer/](../.devcontainer/) | Python 3.12 + Azure CLI + GitHub CLI. `postCreateCommand` installs `ruff`, `pytest`, `pyyaml`, and `actionlint` (via [install-actionlint.sh](../.devcontainer/install-actionlint.sh)). |

The runner is the source of truth for the HTTP contract with the Foundry data plane — **not** `az cognitiveservices agent invoke` (which does not exist for hosted agents' Responses endpoint).

---

## Build & test

```bash
# Lint (must both exit 0)
actionlint
ruff check scripts/ tests/

# Unit tests (pure-function, no network)
pytest tests/ -q

# Byte-compile the runner
python3 -m compileall -q scripts/

# README-inputs-sync guard
python3 tests/check_readme_inputs.py

# Live smoke test against a deployed agent
az login
python3 scripts/smoke-tests.py \
  --project-endpoint https://<acct>.services.ai.azure.com/api/projects/<proj> \
  --agent-name <deployed-agent> \
  --tests-file examples/smoke-tests.json
```

A clean live run prints `Summary: N/N passed across 1 agent(s)` and exits `0`. Runner errors exit `2`, assertion failures exit `1`.

---

## Key Conventions

### Marketplace requirements — non-negotiable
- `action.yml` **must** stay at repo root. Moving it into a subdirectory removes the "Publish this Action to the GitHub Marketplace" checkbox from the Release page.
- `action.yml` must declare all four Marketplace fields at the top level: `name`, `description`, `author`, `branding` (with both `icon` and `color`).
- The `name` (`AI Smoke Test`) must be unique across the Marketplace. If a collision appears at publish time, fall back to `AI Agent Smoke Test`.
- **`description` must be < 125 characters.** The Marketplace publish form rejects anything longer. Keep the current short form (`Smoke-test Microsoft Foundry hosted agents: POST prompts from a JSON catalog and assert on the reply text.`) unless a rewrite fits in the same budget.
- Never delete or rename `LICENSE` — Marketplace requires an OSI license file.

### Marketplace listing metadata (categories + tags)
- Categories and tags are **not** in `action.yml`; they are set per-release in the GitHub UI (Release page → Marketplace section, or **Edit release** on an existing release).
- The Marketplace listing shows the metadata from the **most recent published release**. Edit the latest release to change what visitors see — no need to cut a new tag.
- **Categories:** primary `Deployment`, secondary `Testing`. Do not swap these silently between releases; users filter by category.
- **Tags:** always apply the curated set from [docs/publishing.md](../docs/publishing.md#categories-and-tags). Do not invent new tags per release, and never add tags for frameworks or protocols the action does not actually work against.

### Composite action rules
- **No `${{ inputs.* }}` interpolation in `run:` shell strings.** Every input reaches the shell via an `env:` var. This is an injection-hardening rule — inputs on a public action are attacker-controllable.
- The runner path uses `${GITHUB_ACTION_PATH}/scripts/smoke-tests.py`, never `./scripts/smoke-tests.py`, so the action works regardless of the caller's CWD or checkout layout.
- Comma-separated `agent_name` is exploded into repeated `--agent-name` flags in bash (`IFS=',' read -ra names`), not passed through as a comma-string — the runner's `action="append"` argparse expects one name per flag.

### Runner rules
- **Stdlib only.** No `requirements.txt`. No pip installs at runtime. If a change needs a third-party library, escalate — it changes the deployment model.
- **Two-tier auth:** `FOUNDRY_TOKEN` env var (CI path) → `az account get-access-token --resource https://ai.azure.com/` fallback (local path). Never add a `token` input to `action.yml` — putting tokens in workflow YAML is a footgun even when wrapped in `${{ secrets.* }}`.
- **Audience is `https://ai.azure.com/`** — tokens scoped to `cognitiveservices.azure.com` return `401` from the Responses endpoint.
- **Exit codes are load-bearing:** `0` all pass, `1` at least one assertion failed, `2` runner error (missing catalog, empty catalog, `az` failure). CI logic depends on this split.
- **Do not catch `URLError`/timeout** in `post_response`. Connection-level failures must crash the runner so an unreachable agent fails loudly instead of masquerading as an assertion failure.
- **Smart-quote folding** (`_ascii_fold`) happens before every substring comparison. Any new matcher must apply it too, otherwise catalogs written with ASCII apostrophes will silently miss replies containing typographic quotes.
- **Preview logging on failure:** every assertion failure must print at least the first 300 chars of the reply. Empty text after a `200 OK` must dump `payload keys` and `raw body` — that ambiguity (empty response vs. `extract_text` shape drift) is the single most common false-negative mode.
- **API version is pinned** (`API_VERSION = "2025-11-15-preview"`). Bump only when a coordinated hosted-agent release requires it, and add a release note calling out the version change.

### Catalog schema — additive-only within a major
- Adding a new top-level field to a test entry (e.g. a new assertion matcher, a new threading key) is a **minor** version bump. Update the README schema table and `examples/smoke-tests.json` in the same PR.
- Renaming or removing a field is a **major** version bump. Do not sneak breaking changes into `@v1`.
- Missing assertion keys are silently skipped, not failed — this is the promise that lets old catalogs keep working when the schema grows.

### Semver + release flow
- Releases are cut **manually** — there is no release workflow. Tag `vMAJOR.MINOR.PATCH` on `main`, force-move the `vMAJOR` moving tag to the same commit, and create the GitHub Release (see [docs/publishing.md](../docs/publishing.md) for the exact commands).
- Callers pin `@v1` (moving) or `@v1.0.0` (immutable). Never advertise `@main` in docs.
- Hotfix path: delete the bad tag locally and remotely, re-tag the correct commit, force-move `vMAJOR`, and recreate the release with `gh release create`.

### CI expectations
- All four CI jobs (`lint-action`, `lint-python`, `unit-tests`, `readme-inputs-sync`) must pass before merge. There is no `main`-only guard — enforce via branch protection.
- `readme-inputs-sync` requires every `action.yml` input to appear in `README.md` **backtick-wrapped** (`` `input_name` ``). Prose mentions don't count — the guard is there to catch drift, not to check spelling.
- `actionlint` is installed in the CI job via the same `install-actionlint.sh` script the devcontainer uses. Keep the script's version pin (`ACTIONLINT_VERSION`) in one place — do not fork the install into per-workflow inline curls.

### GitHub Actions — minimum versions
Use the major-version tag (e.g. `@v7`) which floats to the latest patch. Do not use anything older than the minimums below.

| Action | Minimum |
|---|---|
| `actions/checkout` | `v7` |
| `actions/setup-python` | `v6` |
| `azure/login` | `v3` |

### Verification before commit
- **Any change to `scripts/smoke-tests.py` behaviour:** run the runner end-to-end against a live deployed Foundry agent and paste the `Summary:` line into the PR description. Offline pytest catches pure-function bugs; only a live run catches HTTP contract drift, model-specific text quirks, and threading edge cases.
- **Any change to `action.yml` inputs:** update the README inputs table in the same PR (the `readme-inputs-sync` guard will otherwise fail CI).
- **Any change to `examples/smoke-tests.json` schema:** update the README "Catalog schema" table in the same PR.

---

## Documentation conventions

Documentation lives in two places:

| File | Purpose |
|---|---|
| [README.md](../README.md) | Marketplace-facing docs. Quick start, inputs table, prerequisites, catalog schema, auth, exit codes, versioning. Must stay readable on the Marketplace listing page — no repo-only relative image links. |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Dev loop, coding conventions, PR checklist. |
| [SECURITY.md](../SECURITY.md) | Private security advisory link + supported-versions statement. |
| [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Contributor Covenant v2.1, verbatim. |
| [docs/publishing.md](../docs/publishing.md) | Maintainer runbook for cutting a release and publishing/re-publishing to the Marketplace. |

**Accuracy rule:** read the source file before documenting it. Never document the runner or the action from memory — the API version, matcher semantics, and exit codes all matter.

---

## Do-not

- Do not add a `token` input to `action.yml` — auth stays env-var-only (`FOUNDRY_TOKEN` or `az` fallback).
- Do not add pip dependencies to the runner. Stdlib only.
- Do not interpolate `${{ inputs.* }}` directly into a `run:` shell string — always route through an `env:` var.
- Do not move `action.yml` out of the repo root.
- Do not silently drop or rename existing `action.yml` inputs or catalog fields within a major version.
- Do not use `azurerm` or any Azure SDK Python client — the runner is stdlib-only by design.
- Do not catch `URLError` / socket timeouts in `post_response` — they must crash the runner so unreachable agents are diagnosable.
- Do not commit a runner behaviour change without an end-to-end run against a live agent. Include the `Summary:` line in the PR.
- Do not add `${{ ... }}` template expressions to an action's top-level `name:` or `description:` — GitHub rejects the action at load time.
- Do not skip updating `README.md` when adding an input — the `readme-inputs-sync` CI guard blocks merge.
- Do not delete `LICENSE` or omit `branding` from `action.yml` — both are hard Marketplace requirements.
