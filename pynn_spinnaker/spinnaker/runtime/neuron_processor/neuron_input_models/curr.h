#pragma once

// Common includes
#include "../../common/fixed_point_number.h"
#include "../../common/log.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronInputModels::Curr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronInputModels
{
class Curr
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
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static S1615 GetInputCurrent(MutableState &, const ImmutableState &,
                               S1615 excInput, S1615 inhInput,
                               S1615)
  {
    return (excInput - inhInput);
  }

  static S1615 GetRecordable(RecordingChannel c,
                             const MutableState &, const ImmutableState &,
                             S1615, S1615)
  {
    LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant input recording channel %u", c);
    return 0;
  }

  static void Print(char *stream, const MutableState &, const ImmutableState &);
};
};  // namespace NeuronInputModels
};  // namespace NeuronProcessor