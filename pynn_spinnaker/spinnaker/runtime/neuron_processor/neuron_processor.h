#pragma once

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indices or regions
enum Region
{
  RegionSystem,
  RegionNeuron,
  RegionSynapse,
  RegionInputBuffer,
  RegionBackPropagationOutput,
  RegionSpikeRecording,
  RegionAnalogueRecordingStart,
  RegionAnalogueRecordingEnd = RegionAnalogueRecordingStart + 4,
  RegionProfiler = RegionAnalogueRecordingEnd,
};

// Indexes of application words
enum AppWord
{
  AppWordKey,
  AppWordNumNeurons,
  AppWordMax,
};

enum ProfilerTag
{
  ProfilerTagSynapseShape,
  ProfilerTagUpdateNeurons,
  ProfilerTagApplyBuffer,
};

};  // namespace NeuronProcessor