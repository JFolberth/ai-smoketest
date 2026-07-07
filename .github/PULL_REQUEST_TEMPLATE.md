<!--
Thanks for the PR! Fill this out completely so review can focus on the change.
-->

## Summary

<!-- One paragraph: what changed and why. -->

## Semver impact

- [ ] Patch (bug fix, docs, dependency bump)
- [ ] Minor (additive — new input, new catalog field, new assertion type)
- [ ] Major (input renamed/removed, catalog schema breaking change)

## Checklist

- [ ] `actionlint` passes
- [ ] `ruff check scripts/ tests/` passes
- [ ] `pytest tests/ -q` passes
- [ ] `README.md` inputs table matches `action.yml` (if inputs changed)
- [ ] `examples/smoke-tests.json` updated (if catalog schema changed)
- [ ] End-to-end run against a live Foundry agent (paste the `Summary:` line below for behaviour changes)

## Live-agent verification

<!-- For runner behaviour changes, paste the `Summary: N/N passed across M agent(s)` line here. Delete this section for docs-only or CI-only PRs. -->

## Related issues

Closes #
