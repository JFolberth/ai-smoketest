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

1. Ensure `main` is green.
2. Tag and push:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. The `release.yml` workflow runs on the tag push and does two things:
   - Force-updates the `v1` moving major tag to point at the same commit.
   - Creates a GitHub Release with auto-generated notes.
4. Open the newly-created Release in the GitHub UI.

## Publishing to the Marketplace

On the Release page:

1. Tick the checkbox **"Publish this Action to the GitHub Marketplace"**. If the checkbox is missing, `action.yml` is either not at the repo root or is missing `branding` — fix and re-tag.
2. Accept the Marketplace terms of service (first time only).
3. **Primary category:** *Deployment*. **Secondary category:** *Testing*.
4. Preview the listing — confirm the icon renders and the description reads well.
5. Click **Publish release**.

The listing appears at `https://github.com/marketplace/actions/<name-slug>` within a few minutes.

## Subsequent releases

For patch and minor releases, the same tag-push flow works — the release workflow moves `v1` automatically. On each Release page, tick "Publish this Action to the GitHub Marketplace" again; the listing metadata updates immediately.

For a major bump (`v2.0.0`), the release workflow will create a new moving tag `v2` and leave `v1` where it is. Callers on `@v1` are unaffected until they opt in.

## Hotfix workflow

If a release needs to be re-issued (e.g. wrong commit tagged):

```bash
gh workflow run release.yml -f tag=v1.0.1
```

This runs the release job for an existing tag without needing a new tag push. It moves `v1` to that tag and creates the release if it doesn't already exist.

## References

- [Publishing actions in the GitHub Marketplace](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace)
- [Metadata syntax for GitHub Actions](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions)
- [Setting the icon and color for the Marketplace listing](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions#branding)
