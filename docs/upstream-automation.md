---
title: tidas-sdk Upstream Automation Design
docType: guide
scope: repo
status: active
authoritative: false
owner: tidas-sdk
language: en
whenToUse:
  - when a task changes cross-repo automation between tidas-tools and tidas-sdk
  - when reviewing how upstream generation and release-prep PRs should work
whenToUpdate:
  - when upstream trigger shape, dispatch payload, sync workflow layout, or automation authentication changes
checkPaths:
  - docs/upstream-automation.md
  - scripts/ci/**
  - .github/workflows/sync-from-tidas-tools.yml
  - .github/workflows/tag-release-from-merge.yml
  - .docpact/config.yaml
lastReviewedAt: 2026-07-27
lastReviewedCommit: 79ea567ff53c297e3f5f604e7b5a65411456d2e5
related:
  - ../AGENTS.md
  - ../.docpact/config.yaml
  - ./release-setup.md
  - ./agents/repo-architecture.md
---

# Upstream Automation Design

This document describes the recommended cross-repository automation path for keeping `tidas-sdk` in sync with upstream changes from `tiangong-lca/tidas-tools`.

This is a design document, not a statement that the repository already runs this automation today. The current production release path remains the existing tag-driven workflow until the automation workflows and repository settings are actually introduced.

The goal is:

1. `tidas-tools` changes in a way that affects generated SDK content.
2. `tidas-sdk` regenerates the Python and TypeScript SDKs from the exact upstream commit.
3. If generated output changes, `tidas-sdk` opens a release-prep PR.
4. After the PR is merged, `tidas-sdk` creates package tags.
5. Existing tag-driven release automation publishes the packages.

## Design Principles

- `tidas-sdk` remains the package-owning repository.
- npm and PyPI publishing stay in `tidas-sdk/.github/workflows/publish.yml`.
- `tidas-tools` should trigger sync, not publish packages directly.
- auto-generated code changes should still land through a normal PR for review and local/release verification.
- TypeScript and Python package versions stay independent.

## Recommended Flow

```text
tidas-tools push/merge
  -> detect SDK-relevant upstream change
  -> repository_dispatch to tiangong-lca/tidas-sdk
  -> tidas-sdk sync workflow regenerates SDKs from exact tidas-tools SHA
  -> if no diff: stop
  -> if diff: bump package versions, commit bot branch, open PR
  -> merge PR
  -> tidas-sdk post-merge workflow creates package tag(s)
  -> publish.yml runs from package tag(s)
  -> npm / PyPI release completes
```

## Why This Split

This design keeps ownership aligned:

- `tidas-tools` owns schemas, conversion logic, and the upstream trigger.
- `tidas-sdk` owns generated artifacts, package versions, PR review, tags, and publishing.

That avoids a fragile setup where one repository publishes another repository's packages or silently changes package metadata outside the owning repo.

## Workflow Layout

### 1. `tidas-tools`: upstream change detector

Add a workflow in `tiangong-lca/tidas-tools` that runs on merges to `main` and filters for SDK-relevant paths.

Recommended responsibilities:

- decide whether the merged change should trigger SDK regeneration
- determine which package families are affected:
  - `typescript`
  - `python`
  - `both`
- determine the default version bump:
  - `patch`
  - `minor`
  - `major`
- send a `repository_dispatch` event to `tiangong-lca/tidas-sdk`

Recommended dispatch payload:

```json
{
  "event_type": "tidas_tools_changed",
  "client_payload": {
    "tidas_tools_sha": "<merged commit sha>",
    "packages": ["typescript", "python"],
    "typescript_bump": "patch",
    "python_bump": "patch",
    "reason": "schema update"
  }
}
```

Use `repository_dispatch` instead of `workflow_dispatch` so the sender does not need Actions write permission on the target repository.
`tidas_tools_sha` is mandatory and must be a full 40-character commit; the sync
workflow rejects an empty value or branch/ref fallback.

### 2. `tidas-sdk`: sync and release-prep PR

Add a workflow in `tiangong-lca/tidas-sdk` that runs on:

- `repository_dispatch` with type `tidas_tools_changed`
- optional manual `workflow_dispatch` for recovery or re-run

Current implementation file:

- `.github/workflows/sync-from-tidas-tools.yml`

Recommended responsibilities:

1. check out `tidas-sdk`
2. check out `tiangong-lca/tidas-tools` at `client_payload.tidas_tools_sha`
3. verify that checkout against its Rust `assets/asset-lock.v1.json`
4. regenerate SDKs with:
   - `TIDAS_TOOLS_SOURCE_MODE=auto`
   - `TIDAS_TOOLS_PATH=<checked out tools path>`
   - `TIDAS_TOOLS_SHA=<checked out exact commit>`
5. run local parity checks:
   - `./scripts/ci/verify-typescript-package.sh`
   - `./scripts/ci/verify-python-package.sh`
6. detect whether TypeScript and/or Python outputs changed
7. bump only the affected package version(s) to the next unpublished version in the target registry
8. commit changes to a bot branch
9. open or update a release-prep PR against `main`

Validation-contract safeguard for TypeScript refreshes:

- when regeneration touches localized-text schemas or validation helpers, keep the post-processing that injects `params.validationCode` into custom localized-text issues
- when Flow schemas contain cross-field `if` / `then` conditions, keep the generated Zod/Pydantic type-aware validator post-processing
- confirm the committed TypeScript package still normalizes raw Zod issues into stable `validationIssues` codes for downstream consumers
- call this out in the release-prep PR when the machine-readable validation contract changes

Recommended branch name:

- `automation/tidas-tools-sync-<short-sha>`

Recommended PR body content:

- upstream `tidas-tools` commit SHA
- affected packages
- version bump choice
- generation summary
- verification commands used

### 3. `tidas-sdk`: post-merge auto-tagging

Add a workflow in `tiangong-lca/tidas-sdk` that runs after the automation PR merges to `main`.

Current implementation file:

- `.github/workflows/tag-release-from-merge.yml`

Recommended responsibilities:

1. inspect the merged commit
2. detect which package version(s) changed compared with the previous `main` commit
3. fail early if a target package version already exists in npm or PyPI
4. create release tag(s):
   - `typescript-vX.Y.Z`
   - `python-vX.Y.Z`
5. push those tags

Important constraint:

If the repository still relies on tag pushes to trigger `publish.yml`, the tag push must be created with a GitHub App token or PAT. A tag created with the default workflow `GITHUB_TOKEN` may not trigger the downstream publish workflow as intended.

### 4. `tidas-sdk`: existing publish workflow

No architectural change is required for:

- `.github/workflows/publish.yml`

That workflow should remain the package publishing entrypoint because npm and PyPI Trusted Publishing both bind to the concrete repository workflow identity.

## Required GitHub Configuration

### Authentication

Use one shared GitHub App installed on both repositories, or a tightly scoped fine-grained PAT if an App is not available yet.

GitHub App is preferred because it is easier to audit and rotate.

Recommended permissions:

- `Contents: Read and write`
- `Pull requests: Read and write`
- `Metadata: Read`

If you choose `workflow_dispatch` instead of `repository_dispatch`, also grant:

- `Actions: Read and write`

### Secrets

In `tidas-tools`:

- `TIDAS_SDK_AUTOMATION_TOKEN`
  - fine-grained PAT today, or a future GitHub App installation token minted at runtime
  - must be able to dispatch into `tiangong-lca/tidas-sdk`

In `tidas-sdk`:

- `TIDAS_RELEASE_AUTOMATION_TOKEN`
  - fine-grained PAT today, or a future GitHub App installation token minted at runtime
  - must be able to push automation branches, open PRs, and create release tags

If the same GitHub App is used in both repositories, the workflows can mint installation tokens at runtime instead of storing long-lived PATs.

### Environments and registries

Keep the existing protected release environment:

- `pypi-release`

`npm-release` is optional and should only be added if TypeScript publishes are later gated behind a GitHub environment. If that happens, update the npm Trusted Publisher configuration to use the same environment name.

Keep Trusted Publishing bound to:

- repository: `tiangong-lca/tidas-sdk`
- workflow: `.github/workflows/publish.yml`

If fully unattended publishing is desired, update environment protection rules and trusted publisher expectations deliberately. Otherwise keep release approvals in place and automate only up to tag creation.

## Version Bump Policy

Recommended default policy:

- schema-compatible additive change: `minor`
- generator-only fix with no API break: `patch`
- breaking schema or generated API change: `major`

Implementation options:

- simple mode: `tidas-tools` dispatch payload explicitly includes bump levels
- managed mode: `tidas-tools` labels PRs and the workflow maps labels to bump levels
- conservative mode: default to `patch` and let reviewers adjust the release-prep PR before merge

For the first implementation, conservative mode is the safest.

## Change Detection Rules

Recommended behavior inside the `tidas-sdk` sync workflow:

- if no generated output changes, do not open a PR
- if only TypeScript files changed, bump and release only TypeScript
- if only Python files changed, bump and release only Python
- if both changed, prepare both releases in one PR but create independent tags after merge

Do not force both packages to release together when only one generated surface changed.

## Failure Handling

Recommended safeguards:

- if generation fails, fail the workflow and leave logs in the workflow run
- if verification fails, fail before opening a PR
- if a matching automation PR already exists for the same upstream SHA, update it instead of opening duplicates
- if release tags already exist, fail fast instead of force-pushing or retagging
- if publishing fails after tag creation, recover through the normal tag-based release process instead of rewriting history
