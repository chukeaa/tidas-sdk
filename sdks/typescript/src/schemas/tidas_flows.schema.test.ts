import fs from 'node:fs';
import path from 'node:path';
import { FlowsSchema } from './tidas_flows.schema';

function loadElementaryFlow(): Record<string, any> {
  const fixture = path.resolve(
    __dirname,
    '../../../python/tests/fixtures/flow-validation-parity.json'
  );
  const payload = JSON.parse(
    fs.readFileSync(fixture, 'utf8')
  ) as Record<string, any>;
  const dataSet = payload.flowDataSet;
  dataSet.modellingAndValidation.LCIMethod.typeOfDataSet = 'Elementary flow';
  const info = dataSet.flowInformation.dataSetInformation;
  info.name.baseName[0]['#text'] = 'Production from pyrolysis';
  info['common:synonyms'][0]['#text'] = 'tar; syngas; char';
  return payload;
}

describe('type-aware Flow name validation', () => {
  test('allows an Elementary flow without synthetic name qualifiers', () => {
    expect(FlowsSchema.safeParse(loadElementaryFlow()).success).toBe(true);
  });

  test.each(['Product flow', 'Waste flow', 'Other flow'] as const)(
    'requires both name qualifiers for %s',
    (flowType) => {
      const payload = loadElementaryFlow();
      payload.flowDataSet.modellingAndValidation.LCIMethod.typeOfDataSet =
        flowType;

      const result = FlowsSchema.safeParse(payload);

      expect(result.success).toBe(false);
      if (!result.success) {
        const paths = result.error.issues.map((issue) =>
          issue.path.join('.')
        );
        expect(paths).toContain(
          'flowDataSet.flowInformation.dataSetInformation.name.treatmentStandardsRoutes'
        );
        expect(paths).toContain(
          'flowDataSet.flowInformation.dataSetInformation.name.mixAndLocationTypes'
        );
      }
    }
  );

  test('accepts a Product flow when both name qualifiers are present', () => {
    const payload = loadElementaryFlow();
    payload.flowDataSet.modellingAndValidation.LCIMethod.typeOfDataSet =
      'Product flow';
    const name =
      payload.flowDataSet.flowInformation.dataSetInformation.name;
    name.treatmentStandardsRoutes = [
      { '@xml:lang': 'en', '#text': 'technical grade' },
    ];
    name.mixAndLocationTypes = [
      { '@xml:lang': 'en', '#text': 'at plant' },
    ];

    expect(FlowsSchema.safeParse(payload).success).toBe(true);
  });
});
