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
  RegionBackPropagation,
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
  StatRowRequested,
  StatDelayRowRequested,
  StatWordDelayBuffersNotProcessed,
  StatWordInputBufferOverflows,
  StatWordKeyLookupFail,
  StatWordMax,
};

} // SynapseProcessor