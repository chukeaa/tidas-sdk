#!/usr/bin/env node

import { createHash } from 'node:crypto';
import {
  existsSync,
  readFileSync,
  statSync,
} from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const LOCK_RELATIVE_PATH = 'assets/asset-lock.v1.json';
const LOCK_SCHEMA_VERSION = 'tidas.asset-lock.v1';
const RUNTIME_KINDS = new Set([
  'json-schema',
  'chinese-json-schema',
  'methodology',
  'runtime-ruleset',
  'xsd',
  'xslt',
  'xml-reference',
  'legacy-schema-lock',
]);

function fail(message) {
  throw new Error(message);
}

function isSafeRelativePath(value) {
  return (
    typeof value === 'string' &&
    value.length > 0 &&
    !path.posix.isAbsolute(value) &&
    path.posix.normalize(value) === value &&
    value !== '..' &&
    !value.startsWith('../')
  );
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function readAndVerifyCatalog(repoRootInput) {
  const repoRoot = path.resolve(repoRootInput);
  const lockPath = path.join(repoRoot, LOCK_RELATIVE_PATH);
  if (!existsSync(lockPath)) {
    fail(`Rust asset lock not found: ${lockPath}`);
  }

  const lockBytes = readFileSync(lockPath);
  const lock = JSON.parse(lockBytes.toString('utf8'));
  if (lock.schema_version !== LOCK_SCHEMA_VERSION) {
    fail(
      `Unsupported Rust asset lock version: ${String(lock.schema_version)}`
    );
  }
  if (
    !Array.isArray(lock.source_roots) ||
    lock.source_roots.length === 0 ||
    !Array.isArray(lock.entries) ||
    lock.entries.length === 0
  ) {
    fail('Rust asset lock must contain source_roots and entries');
  }

  const sourceRoots = new Set();
  for (const sourceRoot of lock.source_roots) {
    if (!isSafeRelativePath(sourceRoot)) {
      fail(`Unsafe source root in Rust asset lock: ${String(sourceRoot)}`);
    }
    if (sourceRoots.has(sourceRoot)) {
      fail(`Duplicate source root in Rust asset lock: ${sourceRoot}`);
    }
    sourceRoots.add(sourceRoot);
  }

  let previousPath = '';
  const entries = [];
  for (const entry of lock.entries) {
    if (
      !entry ||
      !isSafeRelativePath(entry.path) ||
      typeof entry.kind !== 'string' ||
      !/^[0-9a-f]{64}$/.test(entry.sha256) ||
      !Number.isSafeInteger(entry.bytes) ||
      entry.bytes < 0
    ) {
      fail(`Invalid entry in Rust asset lock: ${JSON.stringify(entry)}`);
    }
    if (previousPath && previousPath >= entry.path) {
      fail('Rust asset lock entries must be strictly path-sorted and unique');
    }
    previousPath = entry.path;

    const sourceRoot = lock.source_roots.find(
      (candidate) =>
        entry.path === candidate || entry.path.startsWith(`${candidate}/`)
    );
    if (!sourceRoot) {
      fail(`Asset is outside every declared source root: ${entry.path}`);
    }

    const absolutePath = path.join(repoRoot, ...entry.path.split('/'));
    if (!existsSync(absolutePath) || !statSync(absolutePath).isFile()) {
      fail(`Locked asset is missing: ${entry.path}`);
    }
    const bytes = readFileSync(absolutePath);
    if (bytes.length !== entry.bytes || sha256(bytes) !== entry.sha256) {
      fail(`Locked asset integrity mismatch: ${entry.path}`);
    }
    entries.push({ ...entry, absolutePath, sourceRoot });
  }

  return { repoRoot, lockPath, lockBytes, lock, entries };
}

function uniqueDirectoryForKind(catalog, kind) {
  const directories = new Set(
    catalog.entries
      .filter((entry) => entry.kind === kind)
      .map((entry) => path.dirname(entry.absolutePath))
  );
  if (directories.size !== 1) {
    fail(
      `Expected exactly one directory for asset kind ${kind}; found ${directories.size}`
    );
  }
  return [...directories][0];
}

function runtimeRoots(catalog) {
  const roots = [];
  const names = new Set();
  for (const sourceRoot of catalog.lock.source_roots) {
    const entries = catalog.entries.filter(
      (entry) =>
        entry.sourceRoot === sourceRoot && RUNTIME_KINDS.has(entry.kind)
    );
    if (entries.length === 0) {
      continue;
    }
    const name = path.posix.basename(sourceRoot);
    if (names.has(name)) {
      fail(`Runtime asset root basename is not unique: ${name}`);
    }
    names.add(name);
    roots.push({
      name,
      sourceRoot,
      path: path.join(catalog.repoRoot, ...sourceRoot.split('/')),
    });
  }
  if (roots.length === 0) {
    fail('Rust asset lock declares no runtime asset roots');
  }
  return roots;
}

function verifyRuntimeCopy(catalog, outputRootInput) {
  const outputRoot = path.resolve(outputRootInput);
  const copiedLockPath = path.join(outputRoot, path.basename(LOCK_RELATIVE_PATH));
  if (!existsSync(copiedLockPath)) {
    fail(`Copied Rust asset lock is missing: ${copiedLockPath}`);
  }
  const copiedLock = readFileSync(copiedLockPath);
  if (!copiedLock.equals(catalog.lockBytes)) {
    fail('Copied Rust asset lock does not match the authoritative upstream lock');
  }

  const selectedRoots = new Map(
    runtimeRoots(catalog).map((root) => [root.sourceRoot, root])
  );
  for (const entry of catalog.entries) {
    const root = selectedRoots.get(entry.sourceRoot);
    if (!root || !RUNTIME_KINDS.has(entry.kind)) {
      continue;
    }
    const relative = entry.path.slice(entry.sourceRoot.length + 1);
    const copiedPath = path.join(outputRoot, root.name, ...relative.split('/'));
    if (!existsSync(copiedPath)) {
      fail(`Runtime asset copy is missing: ${root.name}/${relative}`);
    }
    const copiedBytes = readFileSync(copiedPath);
    if (
      copiedBytes.length !== entry.bytes ||
      sha256(copiedBytes) !== entry.sha256
    ) {
      fail(`Runtime asset copy integrity mismatch: ${root.name}/${relative}`);
    }
  }
}

function usage() {
  return [
    'Usage:',
    '  tidas-tools-assets.mjs verify <tidas-tools-root>',
    '  tidas-tools-assets.mjs path-for-kind <tidas-tools-root> <asset-kind>',
    '  tidas-tools-assets.mjs runtime-roots <tidas-tools-root>',
    '  tidas-tools-assets.mjs lock-path <tidas-tools-root>',
    '  tidas-tools-assets.mjs verify-runtime-copy <tidas-tools-root> <output-root>',
  ].join('\n');
}

function main() {
  const [command, repoRoot, argument] = process.argv.slice(2);
  if (!command || !repoRoot) {
    fail(usage());
  }
  const catalog = readAndVerifyCatalog(repoRoot);

  switch (command) {
    case 'verify':
      process.stdout.write(
        `${JSON.stringify({
          schemaVersion: catalog.lock.schema_version,
          lockPath: catalog.lockPath,
          entries: catalog.entries.length,
          runtimeRoots: runtimeRoots(catalog).map((root) => root.name),
        })}\n`
      );
      return;
    case 'path-for-kind':
      if (!argument) {
        fail(usage());
      }
      process.stdout.write(`${uniqueDirectoryForKind(catalog, argument)}\n`);
      return;
    case 'runtime-roots':
      process.stdout.write(`${JSON.stringify(runtimeRoots(catalog))}\n`);
      return;
    case 'lock-path':
      process.stdout.write(`${catalog.lockPath}\n`);
      return;
    case 'verify-runtime-copy':
      if (!argument) {
        fail(usage());
      }
      verifyRuntimeCopy(catalog, argument);
      process.stdout.write('Runtime asset copy matches the Rust asset lock.\n');
      return;
    default:
      fail(`Unknown command: ${command}\n${usage()}`);
  }
}

try {
  main();
} catch (error) {
  process.stderr.write(
    `error: ${error instanceof Error ? error.message : String(error)}\n`
  );
  process.exitCode = 1;
}
