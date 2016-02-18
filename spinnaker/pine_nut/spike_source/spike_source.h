#pragma once

namespace SpikeSource
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indices or regions
enum Region
{
  RegionSystem,
  RegionSpikeSource,
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

}  // namespace SpikeSource