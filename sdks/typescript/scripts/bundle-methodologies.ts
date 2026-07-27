#!/usr/bin/env node

/**
 * Bundle methodology files into a single JSON file for browser compatibility
 */

import { existsSync } from 'node:fs';
import fs from 'node:fs/promises';
import path from 'node:path';
import yaml from 'yaml';
import {
  requireTidasToolsMethodologyDir,
  resolveTidasToolsMethodologyDir,
} from './resolve-tidas-tools-path.js';

const OUTPUT_DIR = path.join(__dirname, '../src/data');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'bundled-methodologies.json');

function createMethodologyFilesMapping(methodologyDir: string) {
  return {
    contacts: path.join(methodologyDir, 'tidas_contacts.yaml'),
    contacts_category: path.join(
      methodologyDir,
      'tidas_contacts_category.yaml'
    ),
    data_types: path.join(methodologyDir, 'tidas_data_types.yaml'),
    flowproperties_category: path.join(
      methodologyDir,
      'tidas_flowproperties_category.yaml'
    ),
    flowproperties: path.join(methodologyDir, 'tidas_flowproperties.yaml'),
    flows_elementary_category: path.join(
      methodologyDir,
      'tidas_flows_elementary_category.yaml'
    ),
    flows: path.join(methodologyDir, 'tidas_flows.yaml'),
    lifecyclemodels: path.join(methodologyDir, 'tidas_lifecyclemodels.yaml'),
    lciamethods: path.join(methodologyDir, 'tidas_lciamethods.yaml'),
    lciamethods_category: path.join(
      methodologyDir,
      'tidas_lciamethods_category.yaml'
    ),
    locations_category: path.join(
      methodologyDir,
      'tidas_locations_category.yaml'
    ),
    processes: path.join(methodologyDir, 'tidas_processes.yaml'),
    processes_category: path.join(
      methodologyDir,
      'tidas_processes_category.yaml'
    ),
    sources: path.join(methodologyDir, 'tidas_sources.yaml'),
    sources_category: path.join(methodologyDir, 'tidas_sources_category.yaml'),
    unitgroups: path.join(methodologyDir, 'tidas_unitgroups.yaml'),
    unitgroups_category: path.join(
      methodologyDir,
      'tidas_unitgroups_category.yaml'
    ),
  };
}

/**
 * Read a methodology file and return both the parsed data and original YAML text.
 */
async function readMethodologyFile(filePath: string) {
  const text = await fs.readFile(filePath, 'utf8');
  return {
    data: yaml.parse(text),
    text,
  };
}

async function main() {
  console.log('🚀 Starting methodology bundling process...');

  const methodologyRoot = resolveTidasToolsMethodologyDir();
  if (!methodologyRoot && existsSync(OUTPUT_FILE)) {
    console.warn(
      '⚠️  No tidas-tools source checkout found. Keeping the existing bundled methodologies artifact.'
    );
    return;
  }

  const methodologyDir = requireTidasToolsMethodologyDir(
    'Methodology bundling requires access to the upstream Rust asset lock. Set TIDAS_TOOLS_PATH, place a sibling ../tidas-tools checkout next to this repo, or run ../../scripts/ci/generate-typescript-sdk.sh.'
  );
  const methodologyFilesMapping = createMethodologyFilesMapping(methodologyDir);

  // Ensure output directory exists
  if (!existsSync(OUTPUT_DIR)) {
    await fs.mkdir(OUTPUT_DIR, { recursive: true });
    console.log(`✓ Created output directory: ${OUTPUT_DIR}`);
  }

  // Bundle all methodology files
  const bundledData: Record<string, unknown> = {};
  const bundledTexts: Record<string, string> = {};
  let processedCount = 0;
  let skippedCount = 0;

  for (const [key, filePath] of Object.entries(methodologyFilesMapping)) {
    try {
      if (existsSync(filePath)) {
        console.log(`📖 Reading ${key} from ${filePath}`);
        const { data, text } = await readMethodologyFile(filePath);
        bundledData[key] = data;
        bundledTexts[key] = text;
        processedCount++;
        console.log(`✓ Successfully bundled ${key}`);
      } else {
        console.log(`⚠️  Skipping ${key} (file not found: ${filePath})`);
        skippedCount++;
      }
    } catch (error) {
      console.error(`❌ Error processing ${key}:`, error);
      skippedCount++;
    }
  }

  // Add metadata
  const bundleMetadata = {
    total_files: Object.keys(methodologyFilesMapping).length,
    processed_files: processedCount,
    skipped_files: skippedCount,
    file_list: Object.keys(bundledData),
  };

  const finalBundle = {
    _metadata: bundleMetadata,
    methodologies: bundledData,
    methodologyTexts: bundledTexts,
  };

  // Write the bundled data
  await fs.writeFile(OUTPUT_FILE, JSON.stringify(finalBundle, null, 2), 'utf8');

  console.log(`\n🎉 Bundling completed!`);
  console.log(`📦 Output file: ${OUTPUT_FILE}`);
  console.log(`📊 Processed: ${processedCount} files`);
  console.log(`⏭️  Skipped: ${skippedCount} files`);
  console.log(
    `📋 Bundled methodologies: ${Object.keys(bundledData).join(', ')}`
  );

  // Generate TypeScript declaration file
  await generateTypeDeclaration(bundledData);
}

/**
 * Generate TypeScript declaration file for the bundled data
 */
async function generateTypeDeclaration(bundledData: Record<string, unknown>) {
  const declarationPath = path.join(OUTPUT_DIR, 'bundled-methodologies.d.ts');

  const lines: string[] = [
    '/**',
    ' * TypeScript declarations for bundled methodology data',
    ' * Auto-generated by bundle-methodologies.ts',
    ' */',
    '',
    'export interface BundleMetadata {',
    '  total_files: number;',
    '  processed_files: number;',
    '  skipped_files: number;',
    '  file_list: string[];',
    '}',
    '',
    'export interface BundledMethodologies {',
    '  _metadata: BundleMetadata;',
    '  methodologies: {',
  ];

  // Add type for each methodology
  for (const key of Object.keys(bundledData)) {
    lines.push(`    ${key}?: any;`);
  }

  lines.push(
    '  };',
    '  methodologyTexts: {',
  );

  for (const key of Object.keys(bundledData)) {
    lines.push(`    ${key}?: string;`);
  }

  lines.push(
    '  };',
    '}',
    '',
    'declare const bundledMethodologies: BundledMethodologies;',
    'export default bundledMethodologies;'
  );

  await fs.writeFile(declarationPath, lines.join('\n'), 'utf8');
  console.log(`✓ Generated TypeScript declarations: ${declarationPath}`);
}

if (require.main === module) {
  main().catch(console.error);
}
