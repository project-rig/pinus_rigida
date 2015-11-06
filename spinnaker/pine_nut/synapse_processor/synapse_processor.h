#pragma once

namespace SynapseProcessor
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
enum Region
{
  RegionSystem              = 0,
  RegionKeyLookup           = 3,
  RegionSynapticMatrix      = 4,
  RegionPlasticity          = 5,
  RegionOutputBuffer        = 7,
  RegionProfiler            = 11,
};

// Indexes of application words
enum AppWord
{
  AppWordWeightFixedPoint,
  AppWordNumPostNeurons,
  AppWordMax,
};

} // SynapseProcessor