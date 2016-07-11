#pragma once

namespace SupervisorSynapseProcessor
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
  //RegionPlasticity,
  //RegionOutputBuffer,
  //RegionDelayBuffer,
  //RegionBackPropagationInput,
  RegionProfiler = 7,
  RegionStatistics,
  RegionBackPropagationOutput,
};

// Indices of application words
enum AppWord
{
  //AppWordWeightFixedPoint,
  AppWordNumPostNeurons=1,
  //AppWordFlushMask,
  AppWordMax=3,
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
  //StatDelayRowRequested,
  //StatWordDelayBuffersNotProcessed,
  StatWordInputBufferOverflows = 3,
  StatWordKeyLookupFail,
  StatWordMax,
};

} // SynapseProcessor