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
  RegionSynapseShaping  = 2,
  RegionRecordSpikes    = 10,
  RegionRecordAnalogue1 = 11,
  RegionRecordAnalogue2 = 12,
  RegionProfiler        = 17,
};

// Indexes of application words
enum AppWord
{
  AppWordKey,
  AppWordSimulationDuration,
  AppWordTimerPeriod,
  AppWordNumNeurons,
  AppWordMax,
};

};  // namespace NeuronProcessor