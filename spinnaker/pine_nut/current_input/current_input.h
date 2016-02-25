#pragma once

namespace CurrentInput
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of current input executable regions
enum Region
{
  RegionSystem,
  RegionSpikeSource,
  RegionOutputBuffer,
  RegionOutputWeight,
  RegionSpikeRecording,
  RegionProfiler,
};

// Indexes of application words
enum AppWord
{
  AppWordNumCurrentSources,
  AppWordMax,
};

enum ProfilerTag
{
  ProfilerTagTimerTick,
};

} // CurrentInput