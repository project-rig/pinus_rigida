#pragma once

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indices or regions
enum Region
{
  RegionSystem            = 0,
  RegionNeuron            = 1,
  RegionSynapse           = 2,
  RegionInputBuffer       = 6,
  RegionSpikeRecording    = 8,
  RegionAnalogueRecording = 9,
  RegionProfiler          = 10,
};

// Indexes of application words
enum AppWord
{
  AppWordKey,
  AppWordNumNeurons,
  AppWordMax,
};

};  // namespace NeuronProcessor