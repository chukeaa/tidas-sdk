#!/usr/bin/env bash

# shellcheck shell=bash

TIDAS_TOOLS_REPO_URL="${TIDAS_TOOLS_REPO_URL:-https://github.com/tiangong-lca/tidas-tools.git}"
TIDAS_TOOLS_SHA="${TIDAS_TOOLS_SHA:-6a0db19c3a7c8f92c2ee455ae83a158c5a3f91e1}"
TIDAS_TOOLS_SOURCE_MODE="${TIDAS_TOOLS_SOURCE_MODE:-auto}"

RESOLVED_TIDAS_TOOLS_PATH=""
RESOLVED_TIDAS_TOOLS_IS_TEMP=0
TIDAS_TOOLS_ASSET_RESOLVER=""

upstream_git() {
    (
        unset GIT_ALTERNATE_OBJECT_DIRECTORIES
        unset GIT_COMMON_DIR
        unset GIT_CONFIG
        unset GIT_CONFIG_COUNT
        unset GIT_CONFIG_PARAMETERS
        unset GIT_DIR
        unset GIT_GRAFT_FILE
        unset GIT_INDEX_FILE
        unset GIT_OBJECT_DIRECTORY
        unset GIT_PREFIX
        unset GIT_REPLACE_REF_BASE
        unset GIT_SHALLOW_FILE
        unset GIT_WORK_TREE
        command git "$@"
    )
}

is_tidas_tools_checkout() {
    local candidate="${1:-}"

    [ -n "$candidate" ] && [ -f "$candidate/assets/asset-lock.v1.json" ]
}

verify_tidas_tools_commit() {
    local candidate="${1:?candidate is required}"
    local resolved_sha
    local expected_sha_lower
    local resolved_sha_lower

    if [ -z "$TIDAS_TOOLS_SHA" ]; then
        >&2 echo "[ERROR] TIDAS_TOOLS_SHA must be an exact 40-character commit"
        return 1
    fi
    if [[ ! "$TIDAS_TOOLS_SHA" =~ ^[0-9a-fA-F]{40}$ ]]; then
        >&2 echo "[ERROR] Invalid TIDAS_TOOLS_SHA: $TIDAS_TOOLS_SHA"
        return 1
    fi
    if ! resolved_sha="$(upstream_git -C "$candidate" rev-parse HEAD 2>/dev/null)"; then
        >&2 echo "[ERROR] tidas-tools source is not a Git checkout: $candidate"
        return 1
    fi
    expected_sha_lower="$(printf '%s' "$TIDAS_TOOLS_SHA" | tr '[:upper:]' '[:lower:]')"
    resolved_sha_lower="$(printf '%s' "$resolved_sha" | tr '[:upper:]' '[:lower:]')"
    if [ "$resolved_sha_lower" != "$expected_sha_lower" ]; then
        >&2 echo "[ERROR] tidas-tools source commit mismatch"
        >&2 echo "[ERROR] expected: $TIDAS_TOOLS_SHA"
        >&2 echo "[ERROR] actual:   $resolved_sha"
        return 1
    fi
}

verify_tidas_tools_assets() {
    local candidate="${1:?candidate is required}"

    if [ -z "$TIDAS_TOOLS_ASSET_RESOLVER" ]; then
        >&2 echo "[ERROR] TIDAS_TOOLS_ASSET_RESOLVER is not configured"
        return 1
    fi
    node "$TIDAS_TOOLS_ASSET_RESOLVER" verify "$candidate" >&2
}

resolve_tidas_tools_source() {
    local repo_root="${1:?repo_root is required}"
    local -a candidates=()

    case "$TIDAS_TOOLS_SOURCE_MODE" in
        auto)
            if [ -n "${TIDAS_TOOLS_PATH:-}" ]; then
                candidates+=("$TIDAS_TOOLS_PATH")
            fi

            candidates+=(
                "$repo_root/tidas-tools"
                "$repo_root/../tidas-tools"
            )

            for candidate in "${candidates[@]}"; do
                if is_tidas_tools_checkout "$candidate"; then
                    RESOLVED_TIDAS_TOOLS_PATH="$(cd "$candidate" && pwd)"
                    RESOLVED_TIDAS_TOOLS_IS_TEMP=0
                    verify_tidas_tools_commit "$RESOLVED_TIDAS_TOOLS_PATH"
                    verify_tidas_tools_assets "$RESOLVED_TIDAS_TOOLS_PATH"
                    return 0
                fi
            done
            ;;
        clone)
            ;;
        *)
            >&2 echo "[ERROR] Unsupported TIDAS_TOOLS_SOURCE_MODE: $TIDAS_TOOLS_SOURCE_MODE"
            return 1
            ;;
    esac

    RESOLVED_TIDAS_TOOLS_PATH="$(mktemp -d "${TMPDIR:-/tmp}/tidas-tools.XXXXXX")"
    RESOLVED_TIDAS_TOOLS_IS_TEMP=1

    >&2 echo "[STEP] Syncing tidas-tools into a temporary checkout..."
    upstream_git -C "$RESOLVED_TIDAS_TOOLS_PATH" init --quiet
    upstream_git -C "$RESOLVED_TIDAS_TOOLS_PATH" remote add origin "$TIDAS_TOOLS_REPO_URL"
    upstream_git -C "$RESOLVED_TIDAS_TOOLS_PATH" fetch --depth 1 origin "$TIDAS_TOOLS_SHA" >&2
    upstream_git -C "$RESOLVED_TIDAS_TOOLS_PATH" checkout --detach FETCH_HEAD >&2
    verify_tidas_tools_commit "$RESOLVED_TIDAS_TOOLS_PATH"
    verify_tidas_tools_assets "$RESOLVED_TIDAS_TOOLS_PATH"
}

cleanup_tidas_tools_source() {
    if [ "${RESOLVED_TIDAS_TOOLS_IS_TEMP:-0}" -eq 1 ] && [ -n "${RESOLVED_TIDAS_TOOLS_PATH:-}" ]; then
        rm -rf "$RESOLVED_TIDAS_TOOLS_PATH"
    fi
}
