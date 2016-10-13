#pragma once

// Common includes
#include "../../common/fixed_point_number.h"
#include "../../common/log.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronInputModels::Cond
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronInputModels
{
class Cond
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  enum RecordingChannel
  {
    RecordingChannelGSynExc,
    RecordingChannelGSynInh,
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
    // Excitatory reversal voltage [mV]
    S1615 m_V_RevExc;

    // Inhibitory reversal voltage [mV]
    S1615 m_V_RevInh;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static S1615 GetInputCurrent(MutableState &, const ImmutableState &immutableState,
                               S1615 excInput, S1615 inhInput,
                               S1615 membraneVoltage)
  {
    return MulS1615(excInput, immutableState.m_V_RevExc - membraneVoltage) +
        MulS1615(inhInput, immutableState.m_V_RevInh - membraneVoltage);
  }

  static S1615 GetRecordable(RecordingChannel c,
                             const MutableState &, const ImmutableState &,
                             S1615 excInput, S1615 inhInput)
  {
    switch(c)
    {
      case RecordingChannelGSynExc:
        return excInput;

      case RecordingChannelGSynInh:
        return inhInput;

      default:
        LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant input recording channel %u", c);
        return 0;
    }
  }

  static void Print(char *stream, const MutableState &, const ImmutableState &);
};
};  // namespace NeuronInputModels
};  // namespace NeuronProcessor