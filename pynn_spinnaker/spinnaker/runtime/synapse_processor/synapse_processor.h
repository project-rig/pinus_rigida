#pragma once

namespace SynapseProcessor
{
//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
enum Region
{
  RegionSystem,
  RegionKeyLookup,
  RegionSynapticMatrix,
  RegionPlasticity,
  RegionOutputBuffer,
  RegionDelayBuffer,
  RegionProfiler,
  RegionStatistics,
};

// Indices of application words
enum AppWord
{
  AppWordWeightFixedPoint,
  AppWordNumPostNeurons,
  AppWordMax,
};

enum ProfilerTag
{
  ProfilerTagTimerTick,
  ProfilerTagMCPacketReceived,
  ProfilerTagSetupNextDMARowRead,
  ProfilerTagProcessRow,

};

// Indices of statistic words
enum StatWord
{
  StatWordDelayBuffersNotProcessed,
  StatWordInputBufferOverflows,
  StatWordMax,
};

} // SynapseProcessor