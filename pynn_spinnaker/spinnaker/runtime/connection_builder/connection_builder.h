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
  RegionConnectionBuilder,
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


} // ConnectionBuilder