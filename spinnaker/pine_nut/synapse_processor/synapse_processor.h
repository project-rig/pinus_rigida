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
  RegionKeyLookup           = 4,
  RegionSynapticMatrix      = 5,
  RegionPlasticity          = 6,
  RegionOutputBuffer        = 7,
  RegionProfiler            = 17,
};

// Indexes of application words
enum AppWord
{
  AppWordSimulationDuration,
  AppWordTimerPeriod,
  AppWordMax,
};

} // SynapseProcessor