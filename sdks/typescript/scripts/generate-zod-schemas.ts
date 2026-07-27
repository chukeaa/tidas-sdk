#!/usr/bin/env ts-node

import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Types for dependency analysis
interface DependencyGraph {
  [fileName: string]: string[];
}

interface TypeFileInfo {
  fileName: string;
  filePath: string;
  dependencies: string[];
  isMainType: boolean;
}

// Configuration
const TYPES_DIR = 'src/types';
const SCHEMAS_DIR = 'src/schemas';
const CONFIG_FILE = 'ts-to-zod.config.js';
const CONFIG_SAVE_DIR = 'src/schemas/ts-to-zod-configs';
const SAVE_CONFIG_SNAPSHOTS = process.env.TS_TO_ZOD_DEBUG_CONFIGS === '1';

// Main types to generate schemas for - these are the primary interfaces we want to validate
const MAIN_TYPES = [
  'tidas_contacts',
  'tidas_processes',
  'tidas_flows',
  'tidas_sources',
  'tidas_flowproperties',
  'tidas_unitgroups',
  'tidas_lciamethods',
  'tidas_lifecyclemodels',
];

// Core dependency types that other types depend on
const CORE_DEPENDENCY_TYPES = ['tidas_data_types'];

// Category/enum types that are dependencies
const CATEGORY_DEPENDENCY_TYPES = [
  'tidas_locations_category',
  'tidas_contacts_category',
  'tidas_flowproperties_category',
  'tidas_flows_elementary_category',
  'tidas_flows_product_category',
  'tidas_lciamethods_category',
  'tidas_processes_category',
  'tidas_sources_category',
  'tidas_unitgroups_category',
];

// All types that need to be processed (main + dependencies)
const ALL_PROCESSABLE_TYPES = [
  ...CORE_DEPENDENCY_TYPES,
  ...CATEGORY_DEPENDENCY_TYPES,
  ...MAIN_TYPES,
];

async function generateZodSchemas(): Promise<void> {
  console.log('🚀 Generating Zod schemas from TypeScript types...\n');

  // Generate ts-to-zod configuration
  await generateTsToZodConfig();

  // Ensure schemas directory exists
  if (!fs.existsSync(SCHEMAS_DIR)) {
    fs.mkdirSync(SCHEMAS_DIR, { recursive: true });
  }

  // Clean existing schemas
  console.log('🧹 Cleaning existing schemas...');
  const existingSchemas = fs
    .readdirSync(SCHEMAS_DIR)
    .filter((file) => file.endsWith('.schema.ts'));
  for (const schema of existingSchemas) {
    fs.unlinkSync(path.join(SCHEMAS_DIR, schema));
    console.log(`   🗑️  Removed: ${schema}`);
  }

  // Get dependency-sorted types for processing
  const sortedTypes = await analyzeTypeDependencies();
  const typeNames = sortedTypes.map((t) => t.fileName);

  // Run ts-to-zod with configuration, processing each type in dependency order
  console.log('\n📦 Running ts-to-zod for each type in dependency order...');

  // Process all types using standard config approach
  for (const typeName of typeNames) {
    const configName = typeName.replace('tidas_', '');
    console.log(`🔄 Processing ${typeName}...`);

    try {
      const { stderr } = await execAsync(
        `npx ts-to-zod --config=${configName} --skipValidation`
      );

      const outputFile = path.join(SCHEMAS_DIR, `${typeName}.schema.ts`);
      if (fs.existsSync(outputFile)) {
        console.log(`   ✅ ${typeName}.schema.ts generated successfully`);

        // Post-process the generated schema to fix constraint placement
        await postProcessZodSchema(outputFile);
      } else {
        console.log(`   ❌ ${typeName}.schema.ts failed to generate`);
        if (stderr) {
          console.log(`   📋 Error details:`, stderr);
        }
      }
    } catch (error) {
      console.log(
        `   ❌ Failed to process ${typeName}:`,
        (error as Error).message
      );

      // If ts-to-zod fails, try fallback approach
      console.log(`   🔄 Trying fallback approach for ${typeName}...`);
      await generateFallbackSchema(typeName);
    }
  }

  // Final verification
  console.log('\n✅ Final verification of generated schemas:');
  // Need to include tidas_data_types back for verification
  const allTypeNames = sortedTypes.map((t) => t.fileName);
  const successCount = allTypeNames.filter((typeName) => {
    const outputFile = path.join(SCHEMAS_DIR, `${typeName}.schema.ts`);
    const exists = fs.existsSync(outputFile);
    console.log(`   ${exists ? '✅' : '❌'} ${typeName}.schema.ts`);
    return exists;
  }).length;

  console.log(
    `\n📊 Generated ${successCount}/${allTypeNames.length} schemas successfully`
  );

  // Generate enhanced index file
  await generateSchemasIndex();

  // Clean up config file
  if (fs.existsSync(CONFIG_FILE)) {
    fs.unlinkSync(CONFIG_FILE);
    console.log(`🧹 Cleaned up: ${CONFIG_FILE}`);
  }

  console.log('\n🎉 Zod schema generation completed successfully!');
}

/**
 * Get correct dataset key for each type
 */
function getDataSetKeyForType(typeName: string): string {
  switch (typeName) {
    case 'tidas_contacts':
      return 'contactDataSet';
    case 'tidas_processes':
      return 'processDataSet';
    case 'tidas_flows':
      return 'flowDataSet';
    case 'tidas_sources':
      return 'sourceDataSet';
    case 'tidas_flowproperties':
      return 'flowPropertyDataSet';
    case 'tidas_unitgroups':
      return 'unitGroupDataSet';
    case 'tidas_lciamethods':
      return 'LCIAMethodDataSet';
    case 'tidas_lifecyclemodels':
      return 'lifeCycleModelDataSet';
    default:
      return typeName.replace('tidas_', '') + 'DataSet';
  }
}

/**
 * Post-process generated Zod schema to fix constraint placement
 */
async function postProcessZodSchema(schemaFile: string): Promise<void> {
  const content = fs.readFileSync(schemaFile, 'utf8');
  let fixedContent = content;

  // Fix complex union types that exceed TypeScript compiler limits
  // Add explicit type annotation for complex schemas
  if (
    schemaFile.includes('flows_product_category') ||
    schemaFile.includes('flows_elementary_category') ||
    schemaFile.includes('processes_category') ||
    schemaFile.includes('sources_category') ||
    schemaFile.includes('unitgroups_category') ||
    schemaFile.includes('lciamethods_category') ||
    schemaFile.includes('flowproperties_category') ||
    schemaFile.includes('contacts_category') ||
    schemaFile.includes('locations_category')
  ) {
    // Find all schema exports and add explicit type annotation
    fixedContent = fixedContent.replace(
      /export const (\w+Schema) = (z\.union\(\[[\s\S]*?\]\)|z\.literal\([^)]+\)(?:\.optional\(\))?);/g,
      'export const $1: z.ZodType<any> = $2;'
    );
  }

  // For tidas_data_types, apply manual optimizations instead of automatic fixes
  if (schemaFile.includes('tidas_data_types')) {
    console.log('   ℹ️  Applying manual optimizations for tidas_data_types');

    let manualOptimizations = applyLocalizedTextSchemaOverrides(content);
    manualOptimizations = applyCASNumberSchemaOverrides(manualOptimizations);

    manualOptimizations = manualOptimizations.replace(
      /export const StringMultiLangSchema = z\.union\(\[[\s\S]*?\]\);/,
      `const addRequiredMultiLangIssue = (
  value: unknown,
  ctx: z.RefinementCtx
) => {
  if (Array.isArray(value) && value.length === 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Required',
    });
  }
};

export const StringMultiLangSchema = z.union([
  z.array(LocalizedText500ItemSchema),
  LocalizedText500ItemSchema,
]);

export const RequiredStringMultiLangSchema =
  StringMultiLangSchema.superRefine(addRequiredMultiLangIssue);`
    );

    manualOptimizations = manualOptimizations.replace(
      /export const STMultiLangSchema = z\.union\(\[[\s\S]*?\]\);/,
      `export const STMultiLangSchema = z.union([
  z.array(LocalizedText1000ItemSchema),
  LocalizedText1000ItemSchema,
]);

export const RequiredSTMultiLangSchema =
  STMultiLangSchema.superRefine(addRequiredMultiLangIssue);`
    );

    manualOptimizations = manualOptimizations.replace(
      /export const FTMultiLangSchema = z\.union\(\[[\s\S]*?\]\);/,
      `export const FTMultiLangSchema = z.union([
  z.array(LocalizedTextItemSchema),
  LocalizedTextItemSchema,
]);

export const RequiredFTMultiLangSchema =
  FTMultiLangSchema.superRefine(addRequiredMultiLangIssue);`
    );

    manualOptimizations = applyCommonOtherSchemaOverrides(manualOptimizations);

    if (manualOptimizations !== content) {
      fs.writeFileSync(schemaFile, manualOptimizations, 'utf8');
      console.log(
        '   🔧 Applied manual optimizations to tidas_data_types.schema.ts'
      );
    }

    return; // Skip standard automatic fixes for this file
  }

  // Apply intelligent constraint fixes for all schemas
  // Pattern 1: Fix object-level constraints and move them to #text property
  const newContent1 = fixedContent.replace(
    /('#text':\s*z\.string\(\)),(\s*\}\)\s*\.max\((\d+)\))/g,
    "'#text': z.string().max($3),\n    }))"
  );

  // Pattern 2: Fix array-level constraints and move them to #text property within objects
  const newContent2 = newContent1.replace(
    /('#text':\s*z\.string\(\)),(\s*\}\)\s*\)\s*\.max\((\d+)\))/g,
    "'#text': z.string().max($3),\n    })\n  )"
  );

  // Pattern 3: Fix union-level constraints by identifying and replacing them
  const unionMaxPattern =
    /(\w+Schema = z\.union\(\[[\s\S]*?'#text':\s*z\.string\(\)[\s\S]*?\]\))\.max\((\d+)\);/g;
  const newContent3 = newContent2.replace(
    unionMaxPattern,
    (_, unionPart, maxValue) => {
      const fixedUnion = unionPart.replace(
        /('#text':\s*z\.string\(\))/g,
        `'#text': z.string().max(${maxValue})`
      );
      return `${fixedUnion};`;
    }
  );

  fixedContent = applyRequiredLocalizedTextSchemaOverrides(newContent3);
  if (schemaFile.endsWith('tidas_flows.schema.ts')) {
    fixedContent = applyFlowNameConditionOverride(fixedContent);
  }
  const hasChanges = fixedContent !== content;

  if (hasChanges) {
    fs.writeFileSync(schemaFile, fixedContent, 'utf8');
    console.log(
      `   🔧 Applied constraint fixes to ${path.basename(schemaFile)}`
    );
  }
}

function applyFlowNameConditionOverride(content: string): string {
  if (content.includes('FLOW_NAME_CONDITIONAL_FIELDS')) {
    return content;
  }

  const finalSchemaEnd = '\n});\n';
  if (!content.endsWith(finalSchemaEnd)) {
    throw new Error(
      'Could not attach the Flow name conditional validator to FlowsSchema'
    );
  }
  const schemaStart = content.indexOf('export const FlowsSchema');
  if (schemaStart === -1) {
    throw new Error('Could not find FlowsSchema during Flow post-processing');
  }

  const condition = `
const FLOW_NAME_CONDITIONAL_FIELDS = [
  'treatmentStandardsRoutes',
  'mixAndLocationTypes',
] as const;

`;
  const refinedEnd = `
}).superRefine((value, ctx) => {
  const dataSet = value.flowDataSet;
  if (
    dataSet.modellingAndValidation.LCIMethod.typeOfDataSet ===
    'Elementary flow'
  ) {
    return;
  }

  const name = dataSet.flowInformation.dataSetInformation.name;
  for (const field of FLOW_NAME_CONDITIONAL_FIELDS) {
    if (name[field] === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [
          'flowDataSet',
          'flowInformation',
          'dataSetInformation',
          'name',
          field,
        ],
        message: 'Required',
      });
    }
  }
});
`;

  return `${content.slice(0, schemaStart)}${condition}${content.slice(
    schemaStart,
    -finalSchemaEnd.length
  )}${refinedEnd}`;
}

function applyLocalizedTextSchemaOverrides(content: string): string {
  const languageImport = `import { TIDAS_LANGUAGE_CODES } from './../core/validation/tidas-languages';`;
  const localizedTextPrelude = `const chineseCharacterPattern = /[\\u3400-\\u4DBF\\u4E00-\\u9FFF\\uF900-\\uFAFF]/;
const LOCALIZED_TEXT_ZH_MUST_INCLUDE_CHINESE_CHARACTER_CODE =
  'localized_text_zh_must_include_chinese_character';
const LOCALIZED_TEXT_EN_MUST_NOT_CONTAIN_CHINESE_CHARACTER_CODE =
  'localized_text_en_must_not_contain_chinese_character';

export const TidasLanguageCodeSchema = z.enum(TIDAS_LANGUAGE_CODES);

const addLocalizedTextLanguageChecks = (
  value: { '@xml:lang': string; '#text': string },
  ctx: z.RefinementCtx
) => {
  const lang = value['@xml:lang'];
  const text = value['#text'];

  if (lang === 'zh' && !chineseCharacterPattern.test(text)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['#text'],
      message:
        "@xml:lang value 'zh' must include at least one Chinese character",
      params: {
        validationCode: LOCALIZED_TEXT_ZH_MUST_INCLUDE_CHINESE_CHARACTER_CODE,
      },
    });
  }

  if (lang === 'en' && chineseCharacterPattern.test(text)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['#text'],
      message:
        "@xml:lang value 'en' must not contain Chinese characters",
      params: {
        validationCode: LOCALIZED_TEXT_EN_MUST_NOT_CONTAIN_CHINESE_CHARACTER_CODE,
      },
    });
  }
};

const LocalizedTextItemBaseSchema = z.object({
  '@xml:lang': TidasLanguageCodeSchema,
  '#text': z.string(),
});

export const LocalizedTextItemSchema = LocalizedTextItemBaseSchema.superRefine(
  addLocalizedTextLanguageChecks
);`;

  let updatedContent = content;
  if (!updatedContent.includes("from './../core/validation/tidas-languages'")) {
    updatedContent = updatedContent.replace(
      "import { z } from 'zod';\n",
      `import { z } from 'zod';\n${languageImport}\n`
    );
  }

  updatedContent = replaceExportedSchema(
    updatedContent,
    'LocalizedTextItemSchema',
    localizedTextPrelude
  );

  updatedContent = replaceExportedSchema(
    updatedContent,
    'LocalizedText500ItemSchema',
    `export const LocalizedText500ItemSchema =
  LocalizedTextItemBaseSchema.extend({
    '#text': z.string().max(500),
  }).superRefine(addLocalizedTextLanguageChecks);`
  );

  if (
    updatedContent.includes(
      'export const AnnualSupplyOrProductionVolumeTextItemSchema'
    )
  ) {
    updatedContent = replaceExportedSchema(
      updatedContent,
      'AnnualSupplyOrProductionVolumeTextItemSchema',
      `export const AnnualSupplyOrProductionVolumeTextItemSchema =
  LocalizedTextItemBaseSchema.extend({
    '#text': z
      .string()
      .max(500)
      .regex(/^[+-]?(\\d+(\\.\\d*)?|\\.\\d+)([Ee][+-]?\\d+)?\\s+\\S.*$/),
  }).superRefine(addLocalizedTextLanguageChecks);`
    );
  }

  updatedContent = replaceExportedSchema(
    updatedContent,
    'LocalizedText1000ItemSchema',
    `export const LocalizedText1000ItemSchema =
  LocalizedTextItemBaseSchema.extend({
    '#text': z.string().max(1000),
  }).superRefine(addLocalizedTextLanguageChecks);`
  );

  return updatedContent;
}

function applyCASNumberSchemaOverrides(content: string): string {
  const helperImport = `import {
  CAS_NUMBER_CHECKSUM_ERROR_CODE,
  CAS_NUMBER_PATTERN,
  isValidCASNumber,
} from './../core/validation/cas-number';`;

  let updatedContent = content;
  if (!updatedContent.includes("from './../core/validation/cas-number'")) {
    updatedContent = updatedContent.replace(
      "import { z } from 'zod';\n",
      `import { z } from 'zod';\n${helperImport}\n`
    );
  }

  return replaceExportedSchema(
    updatedContent,
    'CASNumberSchema',
    `export const CASNumberSchema = z
  .string()
  .regex(CAS_NUMBER_PATTERN)
  .superRefine((value, ctx) => {
    if (!CAS_NUMBER_PATTERN.test(value) || isValidCASNumber(value)) {
      return;
    }

    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'CASNumber check digit is invalid',
      params: {
        validationCode: CAS_NUMBER_CHECKSUM_ERROR_CODE,
      },
    });
  });`
  );
}

function applyCommonOtherSchemaOverrides(content: string): string {
  const anyXmlElementSchema = `export const AnyXmlElementSchema: z.ZodType<AnyXmlElement> = z.lazy(() =>
  z.union([
    z.null(),
    z.string(),
    z.number(),
    z.boolean(),
    z.array(AnyXmlElementSchema),
    z.record(z.string(), AnyXmlElementSchema),
  ])
);`;

  const commonOtherSchema = `const commonOtherNamespaceDeclarationPattern =
  /^@xmlns(:[A-Za-z_][A-Za-z0-9_.-]*)?$/;
const commonOtherExtensionElementPattern =
  /^(?!(common|xmlns):)([A-Za-z_][A-Za-z0-9_.-]*:)?[A-Za-z_][A-Za-z0-9_.-]*$/;

export const CommonOtherSchema = z
  .record(z.string(), AnyXmlElementSchema)
  .superRefine((value, ctx) => {
    let hasExtensionElement = false;

    for (const [key, entryValue] of Object.entries(value)) {
      if (commonOtherNamespaceDeclarationPattern.test(key)) {
        if (typeof entryValue !== 'string') {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: [key],
            message: 'Namespace declarations in common:other must be strings',
          });
        }
        continue;
      }

      if (commonOtherExtensionElementPattern.test(key)) {
        hasExtensionElement = true;
        continue;
      }

      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [key],
        message:
          'common:other entries must be namespace declarations or non-common extension elements',
      });
    }

    if (!hasExtensionElement) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          'common:other must include at least one non-common extension element',
      });
    }
  });`;

  let updatedContent = replaceExportedSchema(
    content,
    'AnyXmlElementSchema',
    anyXmlElementSchema
  );
  updatedContent = replaceExportedSchema(
    updatedContent,
    'CommonOtherSchema',
    commonOtherSchema
  );

  return updatedContent;
}

function replaceExportedSchema(
  content: string,
  schemaName: string,
  replacement: string
): string {
  const marker = `export const ${schemaName}`;
  const startIndex = content.indexOf(marker);

  if (startIndex === -1) {
    const fallbackMarker = 'export const GlobalReferenceTypeSchema';
    const fallbackIndex = content.indexOf(fallbackMarker);

    if (fallbackIndex === -1) {
      return `${content.trimEnd()}\n\n${replacement}\n`;
    }

    return `${content.slice(0, fallbackIndex)}${replacement}\n\n${content.slice(
      fallbackIndex
    )}`;
  }

  const nextExportIndex = content.indexOf(
    '\n\nexport const ',
    startIndex + marker.length
  );
  const nextPrivateConstIndex = content.indexOf(
    '\n\nconst ',
    startIndex + marker.length
  );
  const candidateEndIndexes = [nextExportIndex, nextPrivateConstIndex].filter(
    (index) => index !== -1
  );
  const endIndex =
    candidateEndIndexes.length > 0
      ? Math.min(...candidateEndIndexes)
      : content.length;

  return `${content.slice(0, startIndex)}${replacement}${content.slice(endIndex)}`;
}

function applyRequiredLocalizedTextSchemaOverrides(content: string): string {
  let updatedContent = content;

  const requiredLocalizedTextSchemaMappings = [
    {
      baseSchemaName: 'StringMultiLangSchema',
      requiredSchemaName: 'RequiredStringMultiLangSchema',
    },
  ];

  for (const {
    baseSchemaName,
    requiredSchemaName,
  } of requiredLocalizedTextSchemaMappings) {
    updatedContent = updatedContent.replace(
      new RegExp(`(:\\s*)${baseSchemaName}(,)`, 'g'),
      `$1${requiredSchemaName}$2`
    );

    updatedContent = syncRequiredLocalizedTextSchemaImport(
      updatedContent,
      baseSchemaName,
      requiredSchemaName
    );
  }

  return updatedContent;
}

function syncRequiredLocalizedTextSchemaImport(
  content: string,
  baseSchemaName: string,
  requiredSchemaName: string
): string {
  const importPattern =
    /import \{\n([\s\S]*?)\n\} from '\.\/tidas_data_types\.schema';/;
  const importMatch = importPattern.exec(content);

  if (!importMatch) {
    return content;
  }

  const importBlock = importMatch[0];
  const importLines = importMatch[1]
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/,$/, ''));

  const contentWithoutImport = content.slice(
    content.indexOf(importBlock) + importBlock.length
  );
  const usesBaseSchema = hasIdentifierReference(
    contentWithoutImport,
    baseSchemaName
  );
  const usesRequiredSchema = hasIdentifierReference(
    contentWithoutImport,
    requiredSchemaName
  );

  if (!usesRequiredSchema) {
    return content;
  }

  if (!importLines.includes(requiredSchemaName)) {
    const baseImportIndex = importLines.indexOf(baseSchemaName);

    if (baseImportIndex >= 0) {
      importLines.splice(baseImportIndex + 1, 0, requiredSchemaName);
    } else {
      importLines.push(requiredSchemaName);
    }
  }

  if (!usesBaseSchema) {
    const baseImportIndex = importLines.indexOf(baseSchemaName);

    if (baseImportIndex >= 0) {
      importLines.splice(baseImportIndex, 1);
    }
  }

  const updatedImportBlock = `import {\n${importLines
    .map((line) => `  ${line},`)
    .join('\n')}\n} from './tidas_data_types.schema';`;

  return content.replace(importBlock, updatedImportBlock);
}

function hasIdentifierReference(content: string, identifier: string): boolean {
  const escapedIdentifier = identifier.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`\\b${escapedIdentifier}\\b`).test(content);
}

/**
 * Generate fallback schema when ts-to-zod fails
 */
async function generateFallbackSchema(typeName: string): Promise<void> {
  const outputFile = path.join(SCHEMAS_DIR, `${typeName}.schema.ts`);
  const dataSetKey = getDataSetKeyForType(typeName);
  const schemaName =
    typeName
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join('') + 'Schema';

  // Create a basic schema that imports from data types and exports a permissive schema
  const fallbackContent = `// Generated fallback schema for ${typeName}
import { z } from 'zod';

// Import base types (this might need manual adjustment)
import {
  UUIDSchema,
  StringMultiLangSchema,
  StringSchema,
  STMultiLangSchema,
  FTMultiLangSchema,
  GlobalReferenceTypeSchema,
  dateTimeSchema
} from './tidas_data_types.schema';

// Fallback schema - allows any structure but provides type checking for common fields
export const ${schemaName} = z.object({
  ${dataSetKey}: z.object({
    // Common XML namespace attributes
    '@xmlns': z.string().optional(),
    '@xmlns:common': z.string().optional(),
    '@xmlns:xsi': z.string().optional(),
    '@version': z.string().optional(),
    '@xsi:schemaLocation': z.string().optional(),
    
    // Allow any additional properties
  }).passthrough()
}).passthrough();

// Note: This is a fallback schema. For full validation, 
// the schema should be manually refined based on the actual type structure.
`;

  try {
    fs.writeFileSync(outputFile, fallbackContent, 'utf8');
    console.log(`   ✅ Generated fallback schema: ${outputFile}`);
  } catch (error) {
    console.log(
      `   ❌ Failed to generate fallback schema: ${(error as Error).message}`
    );
  }
}

/**
 * Analyze TypeScript files to understand their import dependencies
 */
async function analyzeTypeDependencies(): Promise<TypeFileInfo[]> {
  console.log('🔍 Analyzing TypeScript dependencies...');

  const typesFiles = fs
    .readdirSync(TYPES_DIR)
    .filter((file) => file.startsWith('tidas_') && file.endsWith('.ts'))
    .map((file) => file.replace('.ts', ''));

  console.log(`   Found ${typesFiles.length} TypeScript files`);

  const dependencyGraph: DependencyGraph = {};
  const typeFileInfos: TypeFileInfo[] = [];

  // Build dependency graph by parsing import statements
  for (const fileName of typesFiles) {
    const filePath = path.join(TYPES_DIR, `${fileName}.ts`);
    const content = fs.readFileSync(filePath, 'utf8');

    const dependencies = parseImportStatements(content, fileName);
    dependencyGraph[fileName] = dependencies;

    typeFileInfos.push({
      fileName,
      filePath,
      dependencies,
      isMainType: ALL_PROCESSABLE_TYPES.includes(fileName),
    });
  }

  // Filter to only include types we want to process
  const processableTypes = typeFileInfos.filter((info) => info.isMainType);

  console.log(
    `   Analyzed dependencies for ${processableTypes.length} processable types`
  );

  // Sort types based on dependencies using topological sort
  const sortedTypes = topologicalSort(processableTypes, dependencyGraph);

  // Display dependency information
  console.log('\n📊 Dependency Analysis Results:');
  sortedTypes.forEach((typeInfo, index) => {
    const depsList =
      typeInfo.dependencies.length > 0
        ? typeInfo.dependencies.join(', ')
        : 'none';
    console.log(`   ${index + 1}. ${typeInfo.fileName} (deps: ${depsList})`);
  });

  return sortedTypes;
}

/**
 * Parse import statements from TypeScript file content
 */
function parseImportStatements(
  content: string,
  currentFileName: string
): string[] {
  const dependencies: string[] = [];
  const importRegex =
    /import\s+(?:type\s+)?{[^}]+}\s+from\s+['"]\.\/([^'"]+)['"]/g;

  let match: RegExpExecArray | null;
  while ((match = importRegex.exec(content)) !== null) {
    const importedFile = match[1];
    // Only track dependencies on tidas_ files to avoid circular references
    if (importedFile.startsWith('tidas_') && importedFile !== currentFileName) {
      dependencies.push(importedFile);
    }
  }

  return [...new Set(dependencies)]; // Remove duplicates
}

/**
 * Topological sort to determine correct processing order
 */
function topologicalSort(
  types: TypeFileInfo[],
  dependencyGraph: DependencyGraph
): TypeFileInfo[] {
  const visited = new Set<string>();
  const visiting = new Set<string>();
  const result: TypeFileInfo[] = [];
  const typeMap = new Map(types.map((t) => [t.fileName, t]));

  function visit(fileName: string): void {
    if (visited.has(fileName)) return;

    if (visiting.has(fileName)) {
      console.log(`   ⚠️  Circular dependency detected involving ${fileName}`);
      return;
    }

    visiting.add(fileName);

    // Visit dependencies first
    const dependencies = dependencyGraph[fileName] || [];
    for (const dep of dependencies) {
      // Only process dependencies that are in our types to process
      if (typeMap.has(dep)) {
        visit(dep);
      }
    }

    visiting.delete(fileName);
    visited.add(fileName);

    const typeInfo = typeMap.get(fileName);
    if (typeInfo) {
      result.push(typeInfo);
    }
  }

  // Visit all types
  for (const typeInfo of types) {
    visit(typeInfo.fileName);
  }

  return result;
}

/**
 * Generate ts-to-zod configuration file using dependency analysis
 */
async function generateTsToZodConfig(): Promise<void> {
  console.log(
    '⚙️  Generating ts-to-zod configuration with dependency analysis...'
  );

  // Analyze dependencies to get correct processing order
  const sortedTypes = await analyzeTypeDependencies();

  const configs = sortedTypes.map((typeInfo) => ({
    name: typeInfo.fileName.replace('tidas_', ''),
    input: `${TYPES_DIR}/${typeInfo.fileName}.ts`,
    output: `${SCHEMAS_DIR}/${typeInfo.fileName}.schema.ts`,
    getSchemaName: '(id) => `${id}Schema`',
    skipValidation: true,
    keepComments: false,
    skipParseJSDoc: false, // Enable JSDoc parsing for constraint extraction
  }));

  const configContent = `/**
 * ts-to-zod configuration - Auto-generated with dependency analysis
 * Processing order determined by import dependencies
 * @type {import("ts-to-zod").TsToZodConfig}
 */
module.exports = [
${configs
  .map(
    (config) => `  {
    name: "${config.name}",
    input: "${config.input}",
    output: "${config.output}",
    getSchemaName: ${config.getSchemaName},
    skipValidation: ${config.skipValidation},
    keepComments: ${config.keepComments},
    skipParseJSDoc: ${config.skipParseJSDoc}
  }`
  )
  .join(',\n')}
];`;

  fs.writeFileSync(CONFIG_FILE, configContent, 'utf8');

  console.log(
    `   ✅ Generated configuration for ${configs.length} types in dependency order`
  );
  if (SAVE_CONFIG_SNAPSHOTS) {
    if (!fs.existsSync(CONFIG_SAVE_DIR)) {
      fs.mkdirSync(CONFIG_SAVE_DIR, { recursive: true });
    }
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const savedConfigFile = path.join(
      CONFIG_SAVE_DIR,
      `ts-to-zod.config.${timestamp}.js`
    );
    fs.writeFileSync(savedConfigFile, configContent, 'utf8');
    console.log(`   📁 Configuration saved to: ${savedConfigFile}`);
  }
}

async function generateSchemasIndex(): Promise<void> {
  console.log('📋 Generating enhanced schemas index file...');

  // Get all generated schemas
  const _allGeneratedTypes = (await analyzeTypeDependencies()).map(
    (t) => t.fileName
  );

  const indexContent = `/**
 * Automatically generated index file for all Zod schemas
 * Generated with dependency analysis
 */

// Export all schemas

// Re-export commonly used schemas with simpler names
export { ContactsSchema as ContactSchema } from './tidas_contacts.schema';
export { SourcesSchema as SourceSchema } from './tidas_sources.schema';
export { FlowpropertiesSchema as FlowPropertySchema } from './tidas_flowproperties.schema';
export { UnitgroupsSchema as UnitGroupSchema } from './tidas_unitgroups.schema';
export { LciamethodsSchema as LCIAMethodSchema } from './tidas_lciamethods.schema';
export { LifecyclemodelsSchema as LifeCycleModelSchema } from './tidas_lifecyclemodels.schema';
export { FlowsSchema as FlowSchema } from './tidas_flows.schema';
export { ProcessesSchema as ProcessSchema } from './tidas_processes.schema';

// Export category/enum types (if schemas exist)
export { LocationsCategorySchema as LocationCategorySchema } from './tidas_locations_category.schema';
export { ContactSchema as ContactCategorySchema } from './tidas_contacts_category.schema';
export { FlowPropertySchema as FlowPropertyCategorySchema } from './tidas_flowproperties_category.schema';
export { FlowsElementaryCategorySchema as FlowElementaryCategorySchema } from './tidas_flows_elementary_category.schema';
export { FlowsProductCategorySchema as FlowProductCategorySchema } from './tidas_flows_product_category.schema';
export { LCIAMethodSchema as LCIAMethodCategorySchema } from './tidas_lciamethods_category.schema';
export { ProcessesCategorySchema as ProcessCategorySchema } from './tidas_processes_category.schema';
export { SourceSchema as SourceCategorySchema } from './tidas_sources_category.schema';
export { UnitGroupSchema as UnitGroupCategorySchema } from './tidas_unitgroups_category.schema';

// Export validation helper functions
import { z } from 'zod';

export type ValidationResult<T> = {
  success: boolean;
  data?: T;
  error?: z.ZodError;
};

/**
 * Validate data against a Zod schema
 */
export function validateWithZod<T>(
  data: unknown,
  schema: z.ZodSchema<T>
): ValidationResult<T> {
  const result = schema.safeParse(data);
  
  if (result.success) {
    return {
      success: true,
      data: result.data
    };
  } else {
    return {
      success: false,
      error: result.error
    };
  }
}

/**
 * Parse and validate JSON data
 */
export function parseWithZod<T>(
  jsonData: string,
  schema: z.ZodSchema<T>
): ValidationResult<T> {
  try {
    const parsed = JSON.parse(jsonData);
    return validateWithZod(parsed, schema);
  } catch (error) {
    return {
      success: false,
      error: new z.ZodError([{
        code: 'custom',
        message: \`Invalid JSON: \${error instanceof Error ? error.message : 'Unknown error'}\`,
        path: [],
        input: jsonData
      }])
    };
  }
}

/**
 * Batch validate multiple objects
 */
export function validateBatch<T>(
  dataArray: unknown[],
  schema: z.ZodSchema<T>
): ValidationResult<T>[] {
  return dataArray.map(data => validateWithZod(data, schema));
}

/**
 * Create a validation method for object classes
 */
export function createValidationMethod<T>(schema: z.ZodSchema<T>) {
  return function validate(this: any): ValidationResult<T> {
    return validateWithZod(this.data || this._data, schema);
  };
}

/**
 * Create a static validation method for object classes
 */
export function createStaticValidationMethod<T>(schema: z.ZodSchema<T>) {
  return function validateWithSchema(data: unknown): ValidationResult<T> {
    return validateWithZod(data, schema);
  };
}
`;

  const indexFile = path.join(SCHEMAS_DIR, 'index.ts');
  fs.writeFileSync(indexFile, indexContent, 'utf8');
  console.log(`   ✅ Generated: ${indexFile}`);
}

// Run the generator
generateZodSchemas().catch(console.error);
