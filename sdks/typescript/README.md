# TIDAS TypeScript SDK

TypeScript SDK for TIDAS (TianGong Life Cycle Assessment data format) providing type-safe data manipulation, validation, and comprehensive schema support.

## 🚀 Status

**Version**: 0.1.20 (Production Ready)
**Published**: [@tiangong-lca/tidas-sdk](https://www.npmjs.com/package/@tiangong-lca/tidas-sdk)

## ✨ Features

- ✅ **Type-Safe Operations**: Full TypeScript support with generated types
- ✅ **Runtime Validation**: Zod schema validation for all TIDAS data types
- ✅ **Complete Schema Coverage**: Support for all 18 TIDAS data types
- ✅ **Property Access**: Convenient API for accessing nested properties
- ✅ **Object Utilities**: Factory functions and manipulation utilities
- ✅ **JSON Conversion**: Seamless serialization/deserialization
- ✅ **tidas-tools Parity APIs**: Package-level validation compatibility
- ✅ **XML Conversion**: `xmltodict`-backed XML <-> JS object helpers
- ✅ **Directory Tools**: Batch `.json <-> .xml` conversion plus runtime asset copying

## 📦 Installation

```bash
npm install @tiangong-lca/tidas-sdk
```

Node.js `24+` is required.

## 🔧 Quick Start

### Basic Usage

```typescript
import { createTidasContact, TidasContact } from '@tiangong-lca/tidas-sdk';

// Create a contact using factory function
const contact = createTidasContact({
  name: 'Example Organization',
  email: 'contact@example.com',
});

// Access properties with type safety
console.log(contact.name); // "Example Organization"

// Convert to JSON
const json = contact.toJSON();
```

### Advanced Usage

```typescript
import {
  TidasProcess,
  createTidasProcess,
  validateTidasData,
} from '@tiangong-lca/tidas-sdk';

// Create and validate complex objects
const process = createTidasProcess({
  name: 'Manufacturing Process',
  description: 'Production of electronic components',
});

// Validate data
const validation = validateTidasData(process, 'Process');
if (!validation.success) {
  console.error('Validation errors:', validation.errors);
}
```

### tidas-tools Parity APIs

```typescript
import { validatePackageDir } from '@tiangong-lca/tidas-sdk/parity';

const report = validatePackageDir('/path/to/tidas-package');
if (!report.ok) {
  console.error(report.issues);
}
```

### XML Conversion APIs

```typescript
import { datasetFromXml, datasetToXml } from '@tiangong-lca/tidas-sdk/xml';

const dataset = datasetFromXml(xmlPayload);
const xml = datasetToXml(dataset);
```

### Directory Conversion Tools

```typescript
import { convertDirectory } from '@tiangong-lca/tidas-sdk/tools';

await convertDirectory('./input', './output', { toXml: true });
await convertDirectory('./eilcd-data', './tidas-output', { toXml: false });
```

`convertDirectory()` mirrors the non-export behavior of the unified native
`tidas convert` command:

- converts `.json -> .xml` or `.xml -> .json`
- copies non-converted files into `output/data`
- copies the packaged `schemas/`, `stylesheets/`, or `methodologies/` assets into the output root

Database export, ZIP publishing, and S3-related workflows remain in `tidas-tools`.

## 🏗️ Architecture

### Module Structure

```typescript
// Core imports
import {
  // Types
  TidasContact,
  TidasProcess,
  TidasFlow,
  // ... all 18 TIDAS types

  // Factory functions
  createTidasContact,
  createTidasProcess,
  createTidasFlow,
  // ... all factory functions

  // Utilities
  validateTidasData,
  convertToJSON,
  convertFromJSON,
} from '@tiangong-lca/tidas-sdk';

// Individual modules
import { TidasContact } from '@tiangong-lca/tidas-sdk/core';
import { TidasTypes } from '@tiangong-lca/tidas-sdk/types';
import { TidasSchemas } from '@tiangong-lca/tidas-sdk/schemas';
import { TidasUtils } from '@tiangong-lca/tidas-sdk/utils';
```

### Supported TIDAS Data Types

- TidasContact
- TidasFlow
- TidasProcess
- TidasSource
- TidasFlowProperty
- TidasUnitGroup
- TidasLCIAMethod
- TidasLifeCycleModel
- And 10 additional specialized types

## 🧪 Development

### Setup

```bash
# Clone repository
git clone https://github.com/tiangong-lca/tidas-sdk.git
cd tidas-sdk/sdks/typescript

# Install dependencies
npm install

# Build the SDK
npm run build

# Run tests
npm test
```

### Development Commands

```bash
# Development mode (watch)
npm run dev

# Type checking
npm run typecheck

# Linting
npm run lint
npm run lint:fix

# Formatting
npm run format
npm run format:check

# Testing
npm test
npm run test:watch
npm run test:coverage

# Build
npm run clean
npm run build

# Refresh packaged runtime assets from the upstream tidas-tools checkout
npm run sync-runtime-assets
```

### Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

## 📚 Examples

See the [examples](./examples/) directory for comprehensive usage examples:

- [01-basic-usage](./examples/01-basic-usage/) - Basic object creation and manipulation
- [02-object-oriented-usage](./examples/02-object-oriented-usage/) - Advanced patterns
- [03-complete-tidas-entities](./examples/03-complete-tidas-entities/) - All data types

## 🔗 API Reference

### Factory Functions

All TIDAS types have corresponding factory functions:

```typescript
// General pattern
createTidas{Type}(data: Partial<Tidas{Type}>): Tidas{Type}

// Examples
createTidasContact(data)
createTidasProcess(data)
createTidasFlow(data)
```

### Validation

```typescript
// Validate any TIDAS data
const result = validateTidasData(data, 'Contact');
if (result.success) {
  // Data is valid
} else {
  // Handle validation errors
  console.error(result.errors);
}
```

### Property Access

```typescript
// Access nested properties with type safety
const contact = createTidasContact(data);
const email = contact.email; // Type: string | undefined
const address = contact.address?.street; // Type: string | undefined
```

## 📖 Documentation

- **Repository Workflow**: [../../AGENTS.md](../../AGENTS.md)
- **Release Setup**: [../../docs/release-setup.md](../../docs/release-setup.md)
- **Release Guide**: [RELEASE.md](./RELEASE.md)

## 🚀 Release

Normal releases are tag-driven:

```bash
# Validate the package before opening the release PR
./scripts/ci/verify-typescript-package.sh

# After the release PR merges, tag the exact merged commit
git tag typescript-vX.Y.Z
git push origin typescript-vX.Y.Z
```

Version prep helpers are available if you want to update `package.json` locally before committing:

```bash
npm run release:prepare:patch
npm run release:prepare:minor
npm run release:prepare:major
```

## 🤝 Contributing

We welcome contributions! Please:

1. Follow the development guidelines
2. Add tests for new functionality
3. Ensure all tests pass and code is properly formatted
4. Update documentation as needed

## 📄 License

MIT License - see [LICENSE](../LICENSE) file for details.

## 🔗 Related Packages

- [tidas-tools](https://github.com/tiangong-lca/tidas-tools): native `tidas` CLI and integrity-locked upstream schema/methodology assets
- [tidas-python-sdk](../python/): Python SDK (in development)
