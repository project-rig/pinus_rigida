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
  RegionFlush = 4,
  RegionSpikeRecording,
  RegionProfiler,
};

// Indexes of application words
enum AppWord
{
  AppWordSpikeKey,
  AppWordNumNeurons,
  AppWordNumSpikeSources,
  AppWordMax,
};

}  // namespace SpikeSource