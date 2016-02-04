#pragma once

namespace CurrentInputPoisson
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of current input executable regions
enum Region
{
  RegionSystem,
  RegionPoissonSource,
  RegionOutputBuffer,
  RegionOutputWeight,
  RegionSpikeRecording,
};

// Indexes of application words
enum AppWord
{
  AppWordNumCurrentSources,
  AppWordMax,
};

} // CurrentInputPoisson