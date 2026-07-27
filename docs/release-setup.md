---
title: tidas-sdk Release Setup
docType: guide
scope: repo
status: active
authoritative: false
owner: tidas-sdk
language: en
whenToUse:
  - when a task changes release environments, trusted publishing, registry prerequisites, or tag-to-publish workflow behavior
  - when reviewing the release-setup governed doc referenced by docpact routing
whenToUpdate:
  - when publish workflow identity, environment names, secret names, or trusted-publishing prerequisites change
checkPaths:
  - docs/release-setup.md
  - .github/workflows/publish.yml
  - .github/workflows/tag-release-from-merge.yml
  - .docpact/config.yaml
lastReviewedAt: 2026-07-27
lastReviewedCommit: 79ea567ff53c297e3f5f604e7b5a65411456d2e5
related:
  - ../AGENTS.md
  - ../.docpact/config.yaml
  - ./upstream-automation.md
  - ./agents/repo-validation.md
---

# Release Setup

This document captures the one-time repository and registry configuration required for the `tidas-sdk` release workflows.

## Cross-Repository Automation

If you want `tiangong-lca/tidas-tools` changes to automatically rebuild and release the SDK packages in this repository, use the architecture described in [upstream-automation.md](./upstream-automation.md).

Recommended model:

- `tidas-tools` detects SDK-relevant upstream changes
- `tidas-tools` dispatches into `tiangong-lca/tidas-sdk`
- `tidas-sdk` regenerates SDKs from the exact upstream SHA and opens a release-prep PR
- after merge, `tidas-sdk` creates package tags
- the existing `publish.yml` workflow publishes from those tags

Current workflow files:

- `.github/workflows/sync-from-tidas-tools.yml`
- `.github/workflows/tag-release-from-merge.yml`
- `.github/workflows/publish.yml`

Important constraint:

- if tag creation is automated, do not rely on the default workflow `GITHUB_TOKEN` for those tag pushes
- use a GitHub App token or fine-grained PAT so the downstream tag-triggered publish workflow can run as expected
- tag creation runs the relevant package verification script before creating a package tag

Operational preference:

- keep registry ownership and Trusted Publishing configuration in `tiangong-lca/tidas-sdk`
- keep `publish.yml` as the formal package release entrypoint
- automate PR creation and tag creation, not cross-repository direct publishing
- keep `.github/workflows/ci.yml` as manual-dispatch only; ordinary pushes rely on the local pre-push gate
- if a release-prep PR changes the machine-readable TypeScript validation contract, call that out explicitly so downstream consumers can review any UI or API mapping impact before tagging

Required secrets:

- in `tiangong-lca/tidas-sdk`: `TIDAS_RELEASE_AUTOMATION_TOKEN`
- in `tiangong-lca/tidas-tools`: `TIDAS_SDK_AUTOMATION_TOKEN`

The current workflows expect a token that can:

- read `tiangong-lca/tidas-tools`
- push automation branches to `tiangong-lca/tidas-sdk`
- open PRs in `tiangong-lca/tidas-sdk`
- create tag refs in `tiangong-lca/tidas-sdk`
- create a repository dispatch event from `tiangong-lca/tidas-tools` into `tiangong-lca/tidas-sdk`

If you prefer a GitHub App instead of a PAT, keep the same secret names but update the workflows to mint an installation token at runtime.

## GitHub Repository

Create this protected environment in `tiangong-lca/tidas-sdk`:

- `pypi-release`

Recommended settings:

- required reviewers enabled
- prevent self-review enabled
- only maintainers who can approve package releases listed as reviewers

`npm-release` is optional. The current TypeScript publish job uses npm Trusted Publishing without a GitHub deployment environment. Only create `npm-release` if you later decide to gate npm publishes with a GitHub environment, and update the npm Trusted Publisher configuration to match.

The publish workflow file is fixed at:

- `.github/workflows/publish.yml`

Do not rename that workflow file without updating the registry-side trusted publisher configuration.

## npm Trusted Publisher

Configure Trusted Publishing for `@tiangong-lca/tidas-sdk` on npm with:

- organization or user: `tiangong-lca`
- repository: `tidas-sdk`
- workflow filename: `publish.yml`

The TypeScript publish job expects tags named `typescript-vX.Y.Z`.

Leave the environment name unset unless the workflow is explicitly updated to use a GitHub environment for npm releases.

## PyPI Trusted Publisher

Configure a Trusted Publisher for project `tidas-sdk` on PyPI with:

- owner: `tiangong-lca`
- repository name: `tidas-sdk`
- workflow filename: `publish.yml`
- environment name: `pypi-release`

The Python publish job expects tags named `python-vX.Y.Z`.

If the PyPI project does not exist yet, register a pending publisher first so the first trusted publish can create it.

## Repository Settings

- GitHub Actions must be enabled for the repository.
- GitHub-hosted runners must be used for trusted publishing.
- Maintainers should avoid long-lived `NPM_TOKEN` / `PYPI_API_TOKEN` secrets once Trusted Publishing is configured.

## Operational Notes

- `publish.yml` validates that the Git tag matches the package version before upload.
- npm and PyPI releases are independent; configure both publishers even if only one package is released initially.
- if a repository or package rename ever happens, update both the workflow and the trusted publisher registration before the next release.
