#pragma once

// Common includes
#include "../../common/fixed_point_number.h"
#include "../../common/log.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronThresholdModels::Constant
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronThresholdModels
{
class Constant
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  enum RecordingChannel
  {
    RecordingChannelMax,
  };

  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState
  {
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Membrane voltage threshold at which neuron spikes [mV]
    S1615 m_V_Threshold;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline bool HasCrossed(const MutableState &, const ImmutableState &immutableState,
                                S1615 membraneVoltage)
  {
    return (membraneVoltage >= immutableState.m_V_Threshold);
  }

  static S1615 GetRecordable(RecordingChannel c,
                             const MutableState &, const ImmutableState &)
  {
    LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant threshold recording channel %u", c);
    return 0;
  }

  static void Print(char *stream, const MutableState &, const ImmutableState &immutableState);
};
};  // namespace NeuronModels
};  // namespace NeuronProcessor