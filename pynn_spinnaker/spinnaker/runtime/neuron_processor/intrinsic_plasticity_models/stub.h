#pragma once

//-----------------------------------------------------------------------------
// NeuronProcessor::IntrinsicPlasticityModels::Stub
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace IntrinsicPlasticityModels
{
class Stub
{
public:
  //-----------------------------------------------------------------------------
  // Enumerations
  //-----------------------------------------------------------------------------
  enum RecordingChannel
  {
    RecordingChannelMax,
  };

  //-----------------------------------------------------------------------------
  // Public methods
  //-----------------------------------------------------------------------------
  S1615 GetIntrinsicCurrent(unsigned int)
  {
    return 0;
  }

  void ApplySpike(unsigned int, bool)
  {
  }

  bool ReadSDRAMData(uint32_t *, uint32_t, unsigned int)
  {
    return true;
  }

  S1615 GetRecordable(RecordingChannel, unsigned int)
  {
    return 0;
  }
};
} // IntrinsicPlasticityModels
} // NeuronProcessor