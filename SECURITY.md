# Security Policy

## Reporting a vulnerability

Please report security issues privately via GitHub's [private security advisories](https://github.com/JFolberth/ai-smoketest/security/advisories/new) rather than a public issue.

Include:

- A clear description of the vulnerability and its impact.
- Steps to reproduce (workflow YAML, catalog snippet, and any inputs).
- The affected version tag(s) of the action.
- Any suggested mitigation.

You should receive an initial response within 7 days.

## Scope

In scope:

- The `action.yml` composite action definition.
- The bundled runner at `scripts/smoke-tests.py`.
- Anything shipped inside a released tag of this repository.

Out of scope:

- Vulnerabilities in Microsoft Foundry itself (report to Microsoft).
- Vulnerabilities in the caller's workflow YAML (report to the caller).
- The example catalog and sample workflow under `examples/`.

## Supported versions

Only the current major tag receives security fixes. Older majors are not patched — pin to a maintained major (currently `v1`) to receive updates.
