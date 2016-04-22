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
  RegionFlush = 5,
  RegionSpikeRecording,
  RegionProfiler,
};

// Indexes of application words
enum AppWord
{
  AppWordSpikeKey,
  AppWordFlushKey,
  AppWordNumSpikeSources,
  AppWordMax,
};

}  // namespace SpikeSource