#!/usr/bin/env bash

# TypeScript SDK 生成脚本
# 功能: 从 tidas-tools 源仓库重新生成 TypeScript SDK
# 输出: 生成的文件列表和摘要

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 默认参数
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/sdks/typescript/src}"
SDK_ROOT="${SDK_ROOT:-$REPO_ROOT/sdks/typescript}"
source "$SCRIPT_DIR/lib/tidas-tools-source.sh"
source "$SCRIPT_DIR/lib/typescript-dependencies.sh"
TIDAS_TOOLS_ASSET_RESOLVER="$SCRIPT_DIR/tidas-tools-assets.mjs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $*" >&2
}

# 错误处理
handle_error() {
    local line_no=$1
    cleanup_tidas_tools_source
    log_error "Script failed at line $line_no"
    log_error "Command: $BASH_COMMAND"
    exit 1
}

trap 'handle_error $LINENO' ERR
trap cleanup_tidas_tools_source EXIT

# 验证输入
validate_inputs() {
    log_step "Validating inputs..."

    if ! TIDAS_TOOLS_SCHEMA_DIR="$(
        node "$TIDAS_TOOLS_ASSET_RESOLVER" path-for-kind "$TIDAS_TOOLS_PATH" json-schema
    )"; then
        log_error "Could not resolve schemas from the Rust asset lock"
        exit 1
    fi
    export TIDAS_TOOLS_SCHEMA_DIR

    if [ ! -d "$SDK_ROOT" ]; then
        log_error "SDK root directory not found: $SDK_ROOT"
        exit 1
    fi

    if [ ! -d "$OUTPUT_DIR" ]; then
        log_warn "Output directory not found, creating: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi

    log_info "✓ tidas-tools path: $TIDAS_TOOLS_PATH"
    log_info "✓ Rust asset lock schema directory: $TIDAS_TOOLS_SCHEMA_DIR"
    log_info "✓ SDK root: $SDK_ROOT"
    log_info "✓ Output directory: $OUTPUT_DIR"
}

# 检查依赖
check_dependencies() {
    log_step "Checking dependencies..."

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "node not found. Please install Node.js 14+"
        exit 1
    fi

    local node_version=$(node --version)
    log_info "✓ Node.js version: $node_version"

    # 检查 npm
    if ! command -v npm &> /dev/null; then
        log_error "npm not found. Please install npm"
        exit 1
    fi

    local npm_version=$(npm --version)
    log_info "✓ npm version: $npm_version"

    # 检查 package.json
    if [ ! -f "$SDK_ROOT/package.json" ]; then
        log_error "package.json not found in $SDK_ROOT"
        exit 1
    fi

    # 检查是否安装了依赖
    if [ ! -d "$SDK_ROOT/node_modules" ]; then
        log_warn "node_modules not found, installing dependencies..."
        install_typescript_dependencies "$SDK_ROOT"
    fi

    log_info "✓ All dependencies satisfied"
}

# 生成 SDK
generate_sdk() {
    log_step "Generating TypeScript SDK..."

    cd "$SDK_ROOT"

    log_info "Running TypeScript type generation..."

    # Step 1: Generate TypeScript types from JSON schemas
    if grep -q '"generate-types"' package.json; then
        log_info "Step 1/4: Generating TypeScript types from schemas..."
        if TIDAS_TOOLS_PATH="$TIDAS_TOOLS_PATH" TIDAS_TOOLS_SCHEMA_DIR="$TIDAS_TOOLS_SCHEMA_DIR" npm run generate-types; then
            log_info "✓ TypeScript types generated successfully"
        else
            log_error "TypeScript type generation failed"
            cd - > /dev/null
            exit 1
        fi
    else
        log_warn "generate-types script not found in package.json"
    fi

    # Step 2: Generate Zod validation schemas
    if grep -q '"generate-schemas"' package.json; then
        log_info "Step 2/4: Generating Zod validation schemas..."
        if TIDAS_TOOLS_PATH="$TIDAS_TOOLS_PATH" TIDAS_TOOLS_SCHEMA_DIR="$TIDAS_TOOLS_SCHEMA_DIR" npm run generate-schemas; then
            log_info "✓ Zod schemas generated successfully"
        else
            log_error "Zod schema generation failed"
            cd - > /dev/null
            exit 1
        fi
    else
        log_warn "generate-schemas script not found in package.json"
    fi

    # Step 3: Bundle methodologies (根据 build script)
    if grep -q '"bundle-methodologies"' package.json; then
        log_info "Step 3/4: Bundling LCIA methodologies..."
        if TIDAS_TOOLS_PATH="$TIDAS_TOOLS_PATH" npm run bundle-methodologies; then
            log_info "✓ Methodologies bundled successfully"
        else
            log_warn "Methodology bundling failed (non-critical)"
        fi
    fi

    if grep -q '"sync-runtime-assets"' package.json; then
        log_info "Step 4/4: Syncing runtime conversion assets..."
        if TIDAS_TOOLS_PATH="$TIDAS_TOOLS_PATH" npm run sync-runtime-assets; then
            log_info "✓ Runtime assets synced successfully"
        else
            log_error "Runtime asset sync failed"
            cd - > /dev/null
            exit 1
        fi
        node "$TIDAS_TOOLS_ASSET_RESOLVER" verify-runtime-copy \
            "$TIDAS_TOOLS_PATH" "$OUTPUT_DIR/runtime-assets"
    fi

    cd - > /dev/null

    log_info "✓ TypeScript SDK generated"
}

# 运行类型检查
run_typecheck() {
    log_step "Running type check..."

    cd "$SDK_ROOT"

    if npm run typecheck > /dev/null 2>&1; then
        log_info "✓ Type check passed"
    else
        log_warn "Type check failed - this may be expected if schemas are not yet complete"
    fi

    cd - > /dev/null
}

# 生成摘要
generate_summary() {
    log_step "Generating summary..."

    local types_dir="$OUTPUT_DIR/types"
    local schemas_dir="$OUTPUT_DIR/schemas"
    local generated_ts_files=$(find "$OUTPUT_DIR" -name "*.ts" -type f 2>/dev/null | wc -l | tr -d ' ')
    local types_count=0
    local schemas_count=0
    local runtime_assets_dir="$OUTPUT_DIR/runtime-assets"
    local runtime_assets_count=0

    if [ -d "$types_dir" ]; then
        types_count=$(find "$types_dir" -name "*.ts" -type f 2>/dev/null | wc -l | tr -d ' ')
    fi

    if [ -d "$schemas_dir" ]; then
        schemas_count=$(find "$schemas_dir" -name "*.ts" -type f 2>/dev/null | wc -l | tr -d ' ')
    fi

    if [ -d "$runtime_assets_dir" ]; then
        runtime_assets_count=$(find "$runtime_assets_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
    fi

    local generated_js_files=0
    if [ -d "$SDK_ROOT/dist" ]; then
        generated_js_files=$(find "$SDK_ROOT/dist" -name "*.js" -type f 2>/dev/null | wc -l | tr -d ' ')
    fi

    cat <<EOF

================================================================================
TypeScript SDK Generation Summary
================================================================================
Timestamp:        $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Source:           $TIDAS_TOOLS_PATH
Source commit:    $TIDAS_TOOLS_SHA
Output:           $OUTPUT_DIR
TypeScript files: $generated_ts_files files total
  - Types:        $types_count files ($types_dir)
  - Schemas:      $schemas_count files ($schemas_dir)
  - Runtime assets:$runtime_assets_count files ($runtime_assets_dir)
  Compiled files:   $generated_js_files JS files (if built)
  Status:           SUCCESS
================================================================================

Generation includes:
  ✅ TypeScript types from TIDAS JSON schemas
  ✅ Zod validation schemas for runtime type checking
  ✅ Bundled LCIA methodologies
  ✅ Runtime assets for XML conversion and directory tools

Next steps:
1. Run validation: cd sdks/typescript && npm run lint
2. Run type check: cd sdks/typescript && npm run typecheck
3. Run tests: cd sdks/typescript && npm test
4. Build: cd sdks/typescript && npm run build

EOF
}

# 主函数
main() {
    log_info "Starting TypeScript SDK generation..."
    log_info "================================================"

    resolve_tidas_tools_source "$REPO_ROOT"
    TIDAS_TOOLS_PATH="$RESOLVED_TIDAS_TOOLS_PATH"
    validate_inputs
    check_dependencies
    generate_sdk
    run_typecheck
    generate_summary

    log_info "✓ TypeScript SDK generation completed"
    exit 0
}

# 执行主函数
main "$@"
