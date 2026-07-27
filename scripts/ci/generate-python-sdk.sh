#!/usr/bin/env bash

# Python SDK generation script
# Rebuilds the auto-generated Pydantic models from the JSON Schemas bundled in
# the tidas-tools source repository.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON_SDK_ROOT="${PYTHON_SDK_ROOT:-$REPO_ROOT/sdks/python}"
OUTPUT_DIR="${OUTPUT_DIR:-$PYTHON_SDK_ROOT/src/tidas_sdk/generated}"
GENERATOR="${GENERATOR:-$PYTHON_SDK_ROOT/scripts/generate_sdk.py}"
source "$SCRIPT_DIR/lib/tidas-tools-source.sh"
TIDAS_TOOLS_ASSET_RESOLVER="$SCRIPT_DIR/tidas-tools-assets.mjs"

SCHEMAS_DIR=""
PYTHON_RUNNER=()

safe_tput() {
    if [ -n "${TERM:-}" ] && command -v tput >/dev/null 2>&1; then
        tput "$@" 2>/dev/null || true
    fi
}

if [ -n "${TERM:-}" ] && command -v tput >/dev/null 2>&1; then
    GREEN="$(safe_tput setaf 2)"
    RED="$(safe_tput setaf 1)"
    YELLOW="$(safe_tput setaf 3)"
    BLUE="$(safe_tput setaf 4)"
    NC="$(safe_tput sgr0)"
else
    GREEN=""
    RED=""
    YELLOW=""
    BLUE=""
    NC=""
fi

log() { printf "%b[INFO]%b %s\n" "$GREEN" "$NC" "$*" >&2; }
warn() { printf "%b[WARN]%b %s\n" "$YELLOW" "$NC" "$*" >&2; }
err() { printf "%b[ERR ]%b %s\n" "$RED" "$NC" "$*" >&2; }
step() { printf "%b[STEP]%b %s\n" "$BLUE" "$NC" "$*" >&2; }

run_python() {
    "${PYTHON_RUNNER[@]}" "$@"
}

handle_error() {
    cleanup_tidas_tools_source
    err "Failure on line $1"
    exit 1
}

trap 'handle_error $LINENO' ERR
trap cleanup_tidas_tools_source EXIT

validate_inputs() {
    step "Validating inputs..."
    if [ ! -d "$SCHEMAS_DIR" ]; then
        err "Schema directory not found: $SCHEMAS_DIR"
        exit 1
    fi
    if [ ! -f "$GENERATOR" ]; then
        err "Generator not found: $GENERATOR"
        exit 1
    fi
    mkdir -p "$OUTPUT_DIR"
    log "Schemas: $SCHEMAS_DIR"
    log "Output:  $OUTPUT_DIR"
}

check_dependencies() {
    step "Checking dependencies..."
    if command -v uv >/dev/null 2>&1; then
        PYTHON_RUNNER=(uv --directory "$PYTHON_SDK_ROOT" run python)
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_RUNNER=(python3)
    else
        err "Neither uv nor python3 was found in PATH"
        exit 1
    fi

    run_python --version
}

generate_models() {
    step "Generating Python models..."
    run_python "$GENERATOR" \
        --schemas "$SCHEMAS_DIR" \
        --output "$OUTPUT_DIR"
}

verify_generation() {
    step "Running basic verification..."
    run_python -m compileall "$PYTHON_SDK_ROOT/src/tidas_sdk" >/dev/null
    PYTHONPATH="$PYTHON_SDK_ROOT/src:${PYTHONPATH:-}" run_python - <<'PY'
try:
    from tidas_sdk import create_process
except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
    print(f"[WARN] Skipping runtime verification: {exc}")
    raise SystemExit(0)

entity = create_process({})
entity.to_json()
print("[INFO] Runtime verification passed")
PY
}

summarize() {
    step "Generation summary"
    local file_count
    file_count=$(find "$OUTPUT_DIR" -maxdepth 1 -name "*.py" | wc -l | tr -d ' ')
    cat <<EOF

================================================================
Python SDK generation completed
================================================================
Schemas directory : $SCHEMAS_DIR
Output directory  : $OUTPUT_DIR
Generated modules : $file_count
Timestamp         : $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Next steps        :
  1. Inspect generated modules under $OUTPUT_DIR
  2. Run ruff/mypy/pytest inside $PYTHON_SDK_ROOT
  3. Commit the refreshed artifacts
================================================================

EOF
}

main() {
    log "Starting Python SDK generation..."
    resolve_tidas_tools_source "$REPO_ROOT"
    TIDAS_TOOLS_PATH="$RESOLVED_TIDAS_TOOLS_PATH"
    SCHEMAS_DIR="$(
        node "$TIDAS_TOOLS_ASSET_RESOLVER" path-for-kind \
            "$TIDAS_TOOLS_PATH" json-schema
    )"
    validate_inputs
    check_dependencies
    generate_models
    verify_generation
    summarize
    log "Done."
}

main "$@"
