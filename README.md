# AI Smoke Test

[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-ai--smoketest-blue?logo=github)](https://github.com/marketplace/actions/ai-smoke-test)
[![CI](https://github.com/JFolberth/ai-smoketest/actions/workflows/ci.yml/badge.svg)](https://github.com/JFolberth/ai-smoketest/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

Smoke-test an Azure AI Foundry hosted agent by POSTing prompts from a JSON catalog to its Responses endpoint and asserting on the returned text.

Use this action as a post-deploy gate in your CI/CD: it fails the job the moment your hosted agent stops answering, drifts off its system prompt, breaks conversation threading, or returns malformed Responses payloads.

> **New here?** Start with the companion blog post: [Smoke Test Microsoft Foundry Agents with GitHub Actions](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/smoke-test-microsoft-foundry-agents-with-github-actions/4531912) — it walks through why smoke tests matter for hosted agents, the scenario patterns this action was built for, and how it fits into the Agent Development Lifecycle. See also [Further reading](#further-reading) at the bottom.

**Works with any hosted agent, regardless of how it was built.** The runner only talks to the Foundry Responses data-plane endpoint — it does not import any Azure or agent SDK. It does not matter whether the agent is a prompt-only agent (system prompt + model, no custom code), or was authored with the Microsoft Agent Framework, Semantic Kernel, LangChain, or LlamaIndex; whether it was defined declaratively, deployed from source code, or shipped as a container image. If it responds on `POST {project_endpoint}/agents/{agent_name}/endpoint/protocols/openai/responses`, this action can smoke-test it.

> **Scope: Responses API only.** This action is intentionally locked to the OpenAI Responses protocol as exposed by Foundry Hosted Agents. It does **not** target the Azure OpenAI Assistants API (`/threads/{id}/runs`, `/threads/{id}/messages`), a self-hosted `invoke` endpoint (Container Apps, Azure Functions, etc.), or the legacy Azure AI Agents `invoke` pattern. If your agent is not reachable at `.../endpoint/protocols/openai/responses`, this action is not the right tool.

---

## Why smoke test a hosted agent?

Deploying a hosted agent "successfully" only proves the control plane accepted the definition — it does not prove the agent actually answers. The [companion blog post](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/smoke-test-microsoft-foundry-agents-with-github-actions/4531912) walks through the motivation in detail; the short version:

- **Fail fast.** Agents can deploy green and still be silent — a missing dependency, a bad model routing, or an expired connection can leave a "healthy" agent that returns nothing when prompted. A smoke test surfaces that in seconds instead of at the first user report.
- **Fast + cheap gate.** Full evaluations (grounding, safety, tool-use scoring) are slow and expensive to run on every deploy. Smoke tests are a lightweight first gate: cheap enough to run on every merge, thorough enough to catch broken deployments, auth regressions, prompt-instruction regressions, and threading breakage.
- **Not a replacement for evaluations — a complement.** Smoke tests answer "is the agent reachable, responding, and following the most basic prompt expectations?". Evaluations answer "how good is the response?". You want both; you can afford to run the first one on every deploy.
- **Repeatable and portable.** The same JSON catalog runs against every agent you point it at — swap the `agent_name` input to smoke-test a canary, a staging deployment, and production in the same workflow.

Typical scenarios worth encoding as smoke tests (all supported by the catalog schema below):

- An on-topic response with expected keywords.
- Thread continuity via `previous_response_id` (stateless chaining).
- Conversation continuity via a platform-managed conversation resource (stateful).
- Refusal of an off-topic question, and no leaking of the off-topic answer.
- Rejection of a fabricated premise (basic hallucination resistance).
- Context-dependent questions where the agent should qualify its answer instead of guessing.

---

## What it does

- POSTs each prompt in your catalog to the agent's Responses data-plane endpoint (`POST {project_endpoint}/agents/{agent_name}/endpoint/protocols/openai/responses`).
- Extracts the reply text from both `output_text` and the structured `output[*].content[*]` blocks.
- Runs case-insensitive substring assertions (`contains_any`, `contains_all`, `contains_none`) with smart-quote folding.
- Supports multi-turn threading via `previous_response_id` and Foundry-managed conversation resources.
- Runs the same catalog against multiple agents in one invocation (comma-separated `agent_name`).
- Exits `0` on all-pass, `1` on any assertion failure, `2` on runner error.

Zero pip dependencies — the runner is pure stdlib Python 3. No SDK coupling — it speaks the Responses HTTP contract directly, so it stays compatible with any framework that deploys to Foundry Hosted Agents.

---

## Quick start

```yaml
name: Deploy and smoke-test

on:
  push:
    branches: [main]

permissions:
  id-token: write   # for azure/login OIDC
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Azure login (OIDC)
        uses: azure/login@v3
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Smoke-test agent
        uses: JFolberth/ai-smoketest@v1
        with:
          project_endpoint: https://myacct.services.ai.azure.com/api/projects/myproject
          agent_name: my-hosted-agent
          tests_file: tests/smoke-tests.json
```

Multiple agents in one step:

```yaml
      - name: Smoke-test both agents
        uses: JFolberth/ai-smoketest@v1
        with:
          project_endpoint: ${{ steps.infra.outputs.project_endpoint }}
          agent_name: image-based-agent,source-code-agent
          tests_file: tests/smoke-tests.json
```

---

## Inputs

| Name | Required | Default | Description |
|---|---|---|---|
| `project_endpoint` | yes | — | Foundry project endpoint URL, e.g. `https://<account>.services.ai.azure.com/api/projects/<project>`. |
| `agent_name` | yes | — | Deployed hosted agent name. Comma-separate to run the catalog against multiple agents in a single step. |
| `tests_file` | yes | — | Path to the smoke-tests JSON catalog, relative to the caller repository root. |
| `timeout` | no | `120` | Per-request timeout in seconds (covers hosted-agent cold start). |

---

## Prerequisites

The calling job must, before this action runs:

1. **Check out the caller's repository** — this action needs to read `tests_file` from the runner filesystem.
   ```yaml
   - uses: actions/checkout@v7
   ```
2. **Provide a Foundry data-plane token** via one of:
   - `azure/login@v3` — the runner shells out to `az account get-access-token --resource https://ai.azure.com/`. Recommended for GitHub-hosted runners using OIDC.
   - `FOUNDRY_TOKEN` environment variable — a pre-acquired bearer token scoped to `https://ai.azure.com/`. Useful when the runner does not have the Azure CLI installed.

### Permissions the runner identity needs

The identity behind the bearer token (the app registration federated to your GitHub OIDC subject, the workflow's service principal, or whoever produced the `FOUNDRY_TOKEN`) needs **data-plane read/write on the target Foundry project** so it can call both `POST /agents/{name}/endpoint/protocols/openai/responses` (every test) and `POST /agents/{name}/endpoint/protocols/openai/conversations` (any test that uses `create_conversation_as`).

The minimum built-in role that grants this is **`Azure AI User`** (role definition GUID `53ca6127-db72-4b80-b1b0-d745d6d5456d`). Grant it **at Foundry project scope** — narrower than the account or subscription, which keeps the smoke-test identity from touching unrelated projects.

Grant it with the Azure CLI:

```bash
az role assignment create \
  --assignee <object-id-or-appId-of-runner-identity> \
  --role "Azure AI User" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>"
```

Notes:

- **Scope matters.** `Azure AI User` at the Foundry *account* or *resource group* scope also works, but grants access to every project under that scope. Prefer project scope for CI identities.
- **Wrong token audience → 401.** The audience must be `https://ai.azure.com/`. Tokens issued for `https://cognitiveservices.azure.com/` are rejected by the Responses endpoint even when the identity has the right role.
- **Missing role → 403.** If the token is well-formed but the identity is not assigned `Azure AI User` (or an equivalent higher-privilege role) on the project, the first `POST /responses` returns `403` and the runner exits with code `1`.
- **Wrong project or agent name → 404.** Check the `project_endpoint` and `agent_name` inputs against your deployment outputs.
- **No control-plane permissions needed.** The runner never calls management.azure.com; it only hits the Foundry data plane. Roles like `Contributor` on the resource group are unnecessary and over-privileged.

---

## Catalog schema

A catalog is a JSON document with a top-level `tests` array. Each entry is one HTTP step and runs in order. See [`examples/smoke-tests.json`](./examples/smoke-tests.json) for a runnable template.

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Unique step identifier printed in the log. |
| `description` | string | Human-readable purpose (optional but recommended). |
| `prompt` | string | The message sent to the agent. Omit for a setup-only step (see `create_conversation_as`). |
| `assertions.status` | int | Expected HTTP status. Default `200`. |
| `assertions.contains_any` | string[] | Pass if the reply contains **any** of these substrings (case-insensitive, smart-quotes folded). |
| `assertions.contains_all` | string[] | Pass if the reply contains **every** substring. |
| `assertions.contains_none` | string[] | Pass if the reply contains **none** of these substrings. |
| `save_response_id_as` | string | After a successful reply, store its `id` under this key for a later turn to reference. |
| `use_previous_response_id` | string | Send this turn with `previous_response_id` set to a previously-saved id. |
| `create_conversation_as` | string | Setup-only step: `POST /conversations` and store the returned id under this key. No prompt, no assertions. |
| `use_conversation` | string | Send this turn bound to a previously-created conversation id (instead of `previous_response_id`). |

Assertions are case-insensitive substring checks. Missing assertion keys are skipped, not failed. Empty text after a `200 OK` is treated as an assertion failure and the raw payload is dumped to the log for debugging.

---

## Auth

Token acquisition, in priority order:

1. `FOUNDRY_TOKEN` env var — used as-is.
2. `az account get-access-token --resource https://ai.azure.com/` fallback.

The audience **must** be `https://ai.azure.com/`. Tokens scoped to `cognitiveservices.azure.com` are rejected with `401` by this endpoint.

The token is acquired once at the start of the run and reused for every request against every agent. Foundry data-plane tokens last ~60 minutes and a smoke run completes in seconds, so refresh handling is out of scope for this action.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Every test passed for every agent. |
| `1` | Runner started successfully; at least one assertion failed. |
| `2` | Runner error (missing catalog file, empty catalog, `az` token acquisition failed). |

---

## Versioning

- Pinned releases: `JFolberth/ai-smoketest@v1.0.0`.
- Moving major tag: `JFolberth/ai-smoketest@v1` — always points at the latest `v1.x.y` release.
- Bleeding edge: `JFolberth/ai-smoketest@main` — not recommended for production.

Semver: **major** bumps drop or rename inputs, **minor** bumps add inputs or catalog fields, **patch** bumps are runner bug fixes.

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md). The repo ships a devcontainer with Python 3.12, Azure CLI, `actionlint`, `ruff`, and `pytest` pre-installed.

Bug reports and feature requests: use the [issue templates](https://github.com/JFolberth/ai-smoketest/issues/new/choose).

Security issues: see [`SECURITY.md`](./SECURITY.md).

---

## Further reading

- [Smoke Test Microsoft Foundry Agents with GitHub Actions](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/smoke-test-microsoft-foundry-agents-with-github-actions/4531912) — the companion blog post: what smoke tests are for agents, why they belong in the Agent Development Lifecycle, and how they complement (rather than replace) evaluations.

---

## License

[MIT](./LICENSE)
