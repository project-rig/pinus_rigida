#pragma once

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indices or regions
enum Region
{
  RegionSystem                  = 0,
  RegionNeuron                  = 1,
  RegionSynapse                 = 2,
  RegionInputBuffer             = 6,
  RegionSpikeRecording          = 8,
  RegionAnalogueRecordingStart  = 9,
  RegionAnalogueRecordingEnd    = 12,
  RegionProfiler                = RegionAnalogueRecordingEnd,
};

// Indexes of application words
enum AppWord
{
  AppWordKey,
  AppWordNumNeurons,
  AppWordMax,
};

};  // namespace NeuronProcessor