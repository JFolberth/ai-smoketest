# Publishing to the GitHub Marketplace

Maintainer runbook for cutting a release and publishing it to the Marketplace. Anyone with `admin` on `JFolberth/ai-smoketest` can do this.

## Pre-flight (one-time, before v1.0.0)

1. Enable **Discussions** on the repo (Settings → General → Features) — the issue-template `config.yml` links to it.
2. Enable **Private vulnerability reporting** (Settings → Security & analysis).
3. Confirm the repository is public — Marketplace listings require a public repo.
4. Verify `action.yml` at repo root has all Marketplace-required fields:
   - `name` (must be **unique across the Marketplace** — search first).
   - `description` (used verbatim in the listing).
   - `author`.
   - `branding.icon` and `branding.color`.

If the desired `name` is taken, fall back to `AI Agent Smoke Test`.

## Cutting a release

Releases are cut manually. There is no release workflow.

1. Ensure `main` is green.
2. Tag the release commit and push the tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. Force-move the `vMAJOR` moving tag to the same commit so callers pinned to `@v1` pick up the release:
   ```bash
   git tag -f v1 v1.0.0
   git push origin v1 --force
   ```
4. Create the GitHub Release from the tag (UI: **Releases → Draft a new release →** pick `v1.0.0`, click **Generate release notes**, publish). Or from the CLI:
   ```bash
   gh release create v1.0.0 --generate-notes
   ```
5. Open the newly-created Release in the GitHub UI.

## Publishing to the Marketplace

On the Release page:

1. Tick the checkbox **"Publish this Action to the GitHub Marketplace"**. If the checkbox is missing, `action.yml` is either not at the repo root or is missing `branding` — fix and re-tag.
2. Accept the Marketplace terms of service (first time only).
3. **Primary category:** *Deployment*. **Secondary category:** *Testing*.
4. Preview the listing — confirm the icon renders and the description reads well.
5. Click **Publish release**.

The listing appears at `https://github.com/marketplace/actions/<name-slug>` within a few minutes.

## Subsequent releases

For patch and minor releases, repeat the tag + force-move + create-release steps above. On each Release page, tick "Publish this Action to the GitHub Marketplace" again; the listing metadata updates immediately.

For a major bump (`v2.0.0`), create a new moving tag `v2` and leave `v1` where it is. Callers on `@v1` are unaffected until they opt in.

## Hotfix workflow

If a release needs to be re-issued (e.g. wrong commit tagged), delete the bad tag locally and remotely, re-tag the correct commit, force-move `vMAJOR`, and recreate the release:

```bash
git tag -d v1.0.1
git push origin :refs/tags/v1.0.1
git tag v1.0.1 <good-sha>
git push origin v1.0.1
git tag -f v1 v1.0.1
git push origin v1 --force
gh release delete v1.0.1 --yes 2>/dev/null || true
gh release create v1.0.1 --generate-notes
```

## References

- [Publishing actions in the GitHub Marketplace](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace)
- [Metadata syntax for GitHub Actions](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions)
- [Setting the icon and color for the Marketplace listing](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions#branding)
