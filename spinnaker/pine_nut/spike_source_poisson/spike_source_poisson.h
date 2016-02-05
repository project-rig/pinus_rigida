#pragma once

namespace SpikeSourcePoisson
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indices or regions
enum Region
{
  RegionSystem,
  RegionPoissonSource,
  RegionSpikeRecording = 4,
  RegionProfiler,
};

// Indexes of application words
enum AppWord
{
  AppWordKey,
  AppWordNumSpikeSources,
  AppWordMax,
};

}  // namespace SpikeSourcePoisson