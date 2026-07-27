#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TS_ROOT="$REPO_ROOT/sdks/typescript"
source "$SCRIPT_DIR/lib/typescript-dependencies.sh"

snapshot_path_state() {
    local target="$1"
    {
        git -C "$REPO_ROOT" diff --no-ext-diff -- "$target"
        git -C "$REPO_ROOT" ls-files --others --exclude-standard -- "$target"
    }
}

require_stable_generation_output() {
    local target="$1"
    local before_state="$2"
    local after_state

    after_state="$(snapshot_path_state "$target")"
    if [ "$before_state" != "$after_state" ]; then
        echo "error: generation introduced uncommitted changes under '$target'" >&2
        git -C "$REPO_ROOT" status --short -- "$target" >&2
        exit 1
    fi
}

echo "[typescript] installing dependencies"
install_typescript_dependencies "$TS_ROOT"

before_generated_state="$(snapshot_path_state "sdks/typescript/src")"

echo "[typescript] regenerating package sources"
TIDAS_TOOLS_SOURCE_MODE="${TIDAS_TOOLS_SOURCE_MODE:-clone}" \
    "$REPO_ROOT/scripts/ci/generate-typescript-sdk.sh"
require_stable_generation_output "sdks/typescript/src" "$before_generated_state"

echo "[typescript] lint"
(cd "$TS_ROOT" && npm run lint)

echo "[typescript] typecheck"
(cd "$TS_ROOT" && npm run typecheck)

echo "[typescript] test"
(cd "$TS_ROOT" && npm test)

echo "[typescript] build"
(cd "$TS_ROOT" && npm run build)

echo "[typescript] pack dry run"
(cd "$TS_ROOT" && npm pack --dry-run >/dev/null)

echo "[typescript] verification complete"
