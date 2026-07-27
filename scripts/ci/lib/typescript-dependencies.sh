#!/usr/bin/env bash

install_typescript_dependencies() {
    local sdk_root="${1:?TypeScript SDK root is required}"

    if [ ! -f "$sdk_root/package.json" ]; then
        echo "error: package.json not found in $sdk_root" >&2
        return 1
    fi

    if [ ! -f "$sdk_root/package-lock.json" ]; then
        echo "error: package-lock.json not found in $sdk_root" >&2
        return 1
    fi

    if ! command -v npm >/dev/null 2>&1; then
        echo "error: npm not found" >&2
        return 1
    fi

    (
        cd "$sdk_root"
        npm ci --workspaces=false
    )
}
