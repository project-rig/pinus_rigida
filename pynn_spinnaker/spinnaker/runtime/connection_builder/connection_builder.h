#pragma once

namespace ConnectionBuilder
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
enum Region
{
  RegionSystem,
  RegionKeyLookup,
  RegionSynapticMatrix,
  RegionPlasticity,
  RegionOutputBuffer,
  RegionDelayBuffer,
  RegionBackPropagationInput,
  RegionProfiler,
  RegionStatistics,
};

// Indices of application words
enum AppWord
{
  AppWordWeightFixedPoint,
  AppWordNumPostNeurons,
  AppWordFlushMask,
  AppWordMax,
};

// Supported types of synaptic matrix
enum MatrixGeneratorType
{
  MatrixGeneratorTypeStatic,
  MatrixGeneratorTypePlastic,
  MatrixGeneratorTypeExtendedPlastic,
  MatrixGeneratorTypeMax,
};

// Supported types of connector
enum ConnectorGeneratorType
{
  ConnectorGeneratorTypeAllToAll,
  ConnectorGeneratorTypeFixedProbability,
  ConnectorGeneratorTypeOneToOne,
  ConnectorGeneratorTypeFixedNumberPost,
  ConnectorGeneratorTypeFixedNumberPre,
  ConnectorGeneratorTypeMax,
};

// Supported types of parameter
enum ParamGeneratorType
{
  ParamGeneratorTypeConstant,
  ParamGeneratorTypeUniform,
  ParamGeneratorTypeNormal,
  ParamGeneratorTypeNormalClipped,
  ParamGeneratorTypeLogNormal,
  ParamGeneratorTypeMax,
};

} // ConnectionBuilder