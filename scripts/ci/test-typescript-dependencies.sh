#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/typescript-dependencies.sh"

test_root="$(mktemp -d)"
npm_log="$test_root/npm.log"
trap 'find "$test_root" -depth -delete' EXIT

sdk_root="$test_root/typescript"
mkdir -p "$sdk_root"
: >"$sdk_root/package.json"
: >"$sdk_root/package-lock.json"

npm() {
    printf '%s|%s\n' "$PWD" "$*" >>"$npm_log"
}

install_typescript_dependencies "$sdk_root"

expected="$sdk_root|ci --workspaces=false"
actual="$(cat "$npm_log")"
if [ "$actual" != "$expected" ]; then
    echo "error: expected '$expected', got '$actual'" >&2
    exit 1
fi

find "$sdk_root/package-lock.json" -depth -delete
if install_typescript_dependencies "$sdk_root" >"$test_root/missing-lock.stdout" 2>"$test_root/missing-lock.stderr"; then
    echo "error: dependency installation succeeded without package-lock.json" >&2
    exit 1
fi

if ! grep -Fq "package-lock.json not found" "$test_root/missing-lock.stderr"; then
    echo "error: missing lockfile failure did not explain the contract" >&2
    exit 1
fi

if [ "$(wc -l <"$npm_log" | tr -d ' ')" != "1" ]; then
    echo "error: npm was invoked after the lockfile check failed" >&2
    exit 1
fi

grep -Fq 'install_typescript_dependencies "$SDK_ROOT"' "$SCRIPT_DIR/generate-typescript-sdk.sh"
grep -Fq 'install_typescript_dependencies "$TS_ROOT"' "$SCRIPT_DIR/verify-typescript-package.sh"

echo "TypeScript dependency installation contract passed."
