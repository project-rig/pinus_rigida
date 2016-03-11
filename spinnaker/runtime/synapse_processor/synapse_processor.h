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
};

// Indexes of application words
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

} // SynapseProcessor