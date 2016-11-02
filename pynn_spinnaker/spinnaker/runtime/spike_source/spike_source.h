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
  RegionSpikeRecording = 7,
  RegionProfiler,
  RegionStatistics,
};

// Indexes of application words
enum AppWord
{
  AppWordSpikeKey,
  AppWordFlushKey,
  AppWordNumSpikeSources,
  AppWordMax,
};

// Indices of statistic words
enum StatWord
{
  StatWordTaskQueueFull,
  StatWordNumTimerEventOverflows,
  StatWordMax,
};

}  // namespace SpikeSource