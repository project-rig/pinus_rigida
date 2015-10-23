#pragma once

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indices or regions
enum Region
{
  RegionSystem          = 0,
  RegionNeuron          = 1,
  RegionSynapse         = 2,
  RegionInputBuffer     = 6,
  RegionRecordSpikes    = 8,
  RegionRecordAnalogue1 = 9,
  RegionRecordAnalogue2 = 10,
  RegionProfiler        = 11,
};

// Indexes of application words
enum AppWord
{
  AppWordKey,
  AppWordNumNeurons,
  AppWordMax,
};

};  // namespace NeuronProcessor