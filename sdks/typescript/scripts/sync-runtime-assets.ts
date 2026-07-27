import { existsSync } from 'node:fs';
import { cp, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import {
  requireTidasToolsAssetLockPath,
  requireTidasToolsRuntimeRoots,
  resolveTidasToolsRepoRoot,
} from './resolve-tidas-tools-path.js';

const OUTPUT_DIR = path.join(__dirname, '../src/runtime-assets');

async function copyAssetDir(
  sourceDir: string,
  outputRoot: string,
  assetName: string
) {
  const targetDir = path.join(outputRoot, assetName);

  await rm(targetDir, { recursive: true, force: true });
  await cp(sourceDir, targetDir, { recursive: true });
}

async function main() {
  const toolsRoot = resolveTidasToolsRepoRoot();

  if (!toolsRoot) {
    if (existsSync(path.join(OUTPUT_DIR, 'tidas')) && existsSync(path.join(OUTPUT_DIR, 'eilcd'))) {
      console.warn(
        'No tidas-tools checkout found. Keeping existing runtime assets under src/runtime-assets.'
      );
      return;
    }

    requireTidasToolsRuntimeRoots(
      'Runtime asset sync requires access to the upstream tidas-tools repository. Set TIDAS_TOOLS_PATH, place a sibling ../tidas-tools checkout next to this repo, or run ../../scripts/ci/generate-typescript-sdk.sh.'
    );
    return;
  }

  await mkdir(OUTPUT_DIR, { recursive: true });

  for (const assetRoot of requireTidasToolsRuntimeRoots()) {
    await copyAssetDir(assetRoot.path, OUTPUT_DIR, assetRoot.name);
    console.log(`Synced runtime assets: ${assetRoot.name}`);
  }
  await cp(requireTidasToolsAssetLockPath(), path.join(OUTPUT_DIR, 'asset-lock.v1.json'));
  console.log('Synced authoritative Rust asset lock: asset-lock.v1.json');
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
