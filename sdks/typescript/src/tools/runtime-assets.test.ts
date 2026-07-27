import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  copyEilcdAssets,
  copyTidasAssets,
  resolveRuntimeAssetDir,
  resolveRuntimeAssetsDir,
} from './runtime-assets';

function makeTempDir(prefix: string) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

describe('runtime asset helpers', () => {
  it('resolves the packaged runtime asset directories', () => {
    const runtimeAssetsDir = resolveRuntimeAssetsDir();
    const eilcdDir = resolveRuntimeAssetDir('eilcd');
    const tidasDir = resolveRuntimeAssetDir('tidas');

    expect(fs.existsSync(runtimeAssetsDir)).toBe(true);
    expect(fs.existsSync(path.join(eilcdDir, 'schemas'))).toBe(true);
    expect(fs.existsSync(path.join(tidasDir, 'schemas'))).toBe(true);
  });

  it('copies eilcd asset contents into the output root', async () => {
    const outputDir = makeTempDir('tidas-sdk-eilcd-assets-');

    await copyEilcdAssets(outputDir);

    expect(fs.existsSync(path.join(outputDir, 'schemas'))).toBe(true);
    expect(fs.existsSync(path.join(outputDir, 'stylesheets'))).toBe(true);
    expect(fs.existsSync(path.join(outputDir, 'eilcd'))).toBe(false);
  });

  it('copies tidas asset contents into the output root', async () => {
    const outputDir = makeTempDir('tidas-sdk-tidas-assets-');

    await copyTidasAssets(outputDir);

    expect(fs.existsSync(path.join(outputDir, 'schemas'))).toBe(true);
    expect(fs.existsSync(path.join(outputDir, 'methodologies'))).toBe(true);
    expect(fs.existsSync(path.join(outputDir, 'tidas'))).toBe(false);
  });

  it('packages the Rust asset lock and the versioned 10-node taxonomy extension', () => {
    const runtimeAssetsDir = resolveRuntimeAssetsDir();
    const lock = JSON.parse(
      fs.readFileSync(
        path.join(runtimeAssetsDir, 'asset-lock.v1.json'),
        'utf8'
      )
    ) as {
      schema_version: string;
      entries: Array<{
        path: string;
        kind: string;
        sha256: string;
        bytes: number;
      }>;
    };
    const extensionEntry = lock.entries.find(
      (entry) =>
        entry.kind === 'methodology' &&
        path.posix.basename(entry.path) ===
          'elementary_flow_taxonomy_extension.v1.json'
    );
    const extensionPath = path.join(
      runtimeAssetsDir,
      'tidas/methodologies/elementary_flow_taxonomy_extension.v1.json'
    );
    const extensionBytes = fs.readFileSync(extensionPath);
    const extension = JSON.parse(extensionBytes.toString('utf8')) as {
      schema_version: string;
      taxonomy_id: string;
      taxonomy_version: number;
      base_taxonomy: { node_count: number };
      nodes: Array<{ cat_id: string }>;
    };
    const effectiveSchema = JSON.parse(
      fs.readFileSync(
        path.join(
          runtimeAssetsDir,
          'tidas/schemas/tidas_flows_elementary_category.json'
        ),
        'utf8'
      )
    ) as { oneOf: unknown[] };

    expect(lock.schema_version).toBe('tidas.asset-lock.v1');
    expect(lock.entries).toHaveLength(80);
    expect(extensionEntry).toBeDefined();
    expect(extensionBytes).toHaveLength(extensionEntry?.bytes ?? -1);
    expect(createHash('sha256').update(extensionBytes).digest('hex')).toBe(
      extensionEntry?.sha256
    );
    expect(extension).toMatchObject({
      schema_version: 'tidas.elementary-flow-taxonomy-extension.v1',
      taxonomy_id: 'tidas-ef-extension',
      taxonomy_version: 1,
      base_taxonomy: { node_count: 55 },
    });
    expect(extension.nodes).toHaveLength(10);
    expect(effectiveSchema.oneOf).toHaveLength(65);
  });
});
