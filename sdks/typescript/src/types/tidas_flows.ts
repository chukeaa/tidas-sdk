/**
 * This file was automatically generated from tidas_flows
 * DO NOT MODIFY IT BY HAND. Instead, modify the source JSON Schema file,
 * and run the generation script to regenerate this file.
 */

import type {
  CASNumber,
  CommonOther,
  FTMultiLang,
  GlobalReferenceType,
  Int5,
  Perc,
  Real,
  String,
  StringMultiLang,
  UUID,
  Version,
  dateTime,
} from './tidas_data_types';
import type { LocationsCategory } from './tidas_locations_category';

export interface Flows {
  flowDataSet: {
    '@xmlns': 'http://lca.jrc.it/ILCD/Flow';
    '@xmlns:common': 'http://lca.jrc.it/ILCD/Common';
    '@xmlns:ecn': 'http://eplca.jrc.ec.europa.eu/ILCD/Extensions/2018/ECNumber';
    '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance';
    '@version': '1.1';
    '@locations': '../ILCDLocations.xml';
    '@xsi:schemaLocation': 'http://lca.jrc.it/ILCD/Flow ../../schemas/ILCD_FlowDataSet.xsd';
    flowInformation: {
      dataSetInformation: {
        'common:UUID': UUID;
        name: {
          baseName: StringMultiLang;
          treatmentStandardsRoutes?: StringMultiLang;
          mixAndLocationTypes?: StringMultiLang;
          flowProperties?: StringMultiLang;
          'common:other'?: CommonOther;
        };
        'common:synonyms'?: FTMultiLang;
        classificationInformation: any | any;
        CASNumber?: CASNumber;
        sumFormula?: String;
        'common:generalComment'?: FTMultiLang;
        'common:other'?: CommonOther;
      };
      quantitativeReference: {
        referenceToReferenceFlowProperty: Int5;
        'common:other'?: CommonOther;
      };
      geography?: {
        locationOfSupply?: LocationsCategory;
        'common:other'?: CommonOther;
      };
      technology?: {
        technologicalApplicability?: FTMultiLang;
        referenceToTechnicalSpecification?: GlobalReferenceType;
        'common:other'?: CommonOther;
      };
      'common:other'?: CommonOther;
    };
    modellingAndValidation: {
      LCIMethod: {
        typeOfDataSet:
          | 'Elementary flow'
          | 'Product flow'
          | 'Waste flow'
          | 'Other flow';
        'common:other'?: CommonOther;
      };
      complianceDeclarations: {
        compliance:
          | {
              'common:referenceToComplianceSystem': GlobalReferenceType;
              'common:approvalOfOverallCompliance':
                | 'Fully compliant'
                | 'Not compliant'
                | 'Not defined';
              'common:other'?: CommonOther;
            }
          | {
              'common:referenceToComplianceSystem': GlobalReferenceType;
              'common:approvalOfOverallCompliance':
                | 'Fully compliant'
                | 'Not compliant'
                | 'Not defined';
              'common:other'?: CommonOther;
            }[];
        'common:other'?: CommonOther;
      };
      'common:other'?: CommonOther;
    };
    administrativeInformation: {
      dataEntryBy: {
        'common:timeStamp': dateTime;
        'common:referenceToDataSetFormat': GlobalReferenceType;
        'common:referenceToPersonOrEntityEnteringTheData'?: GlobalReferenceType;
        'common:other'?: CommonOther;
      };
      publicationAndOwnership: {
        'common:dataSetVersion': Version;
        'common:referenceToPrecedingDataSetVersion'?: GlobalReferenceType;
        'common:permanentDataSetURI'?: string;
        'common:referenceToOwnershipOfDataSet': GlobalReferenceType;
        'common:other'?: CommonOther;
      };
      'common:other'?: CommonOther;
    };
    flowProperties: {
      flowProperty:
        | {
            '@dataSetInternalID': Int5;
            referenceToFlowPropertyDataSet: GlobalReferenceType;
            meanValue: Real;
            minimumValue?: Real;
            maximumValue?: Real;
            uncertaintyDistributionType?:
              | 'undefined'
              | 'log-normal'
              | 'normal'
              | 'triangular'
              | 'uniform';
            relativeStandardDeviation95In?: Perc;
            dataDerivationTypeStatus?:
              | 'Measured'
              | 'Calculated'
              | 'Estimated'
              | 'Unknown derivation';
            generalComment?: StringMultiLang;
            'common:other'?: CommonOther;
          }
        | {
            '@dataSetInternalID': Int5;
            referenceToFlowPropertyDataSet: GlobalReferenceType;
            meanValue: Real;
            minimumValue?: Real;
            maximumValue?: Real;
            uncertaintyDistributionType?:
              | 'undefined'
              | 'log-normal'
              | 'normal'
              | 'triangular'
              | 'uniform';
            relativeStandardDeviation95In?: Perc;
            dataDerivationTypeStatus?:
              | 'Measured'
              | 'Calculated'
              | 'Estimated'
              | 'Unknown derivation';
            generalComment?: StringMultiLang;
            'common:other'?: CommonOther;
          }[];
      'common:other'?: CommonOther;
    };
    'common:other'?: CommonOther;
  };
}
