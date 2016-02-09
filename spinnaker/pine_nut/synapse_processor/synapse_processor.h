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
  ProfilerTagMCPacketReceived,
  ProfilerTagSetupNextDMARowRead,
  ProfilerProcessRow,

};

} // SynapseProcessor