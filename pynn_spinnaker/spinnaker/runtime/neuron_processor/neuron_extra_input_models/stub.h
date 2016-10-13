#pragma once

// Common includes
#include "../../common/fixed_point_number.h"
#include "../../common/log.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronExtraInputModels::Stub
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronExtraInputModels
{
class Stub
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
                               S1615)
  {
    return 0;
  }

  static void SetSpiked(MutableState &, const ImmutableState &)
  {
  }

  static S1615 GetRecordable(RecordingChannel c,
                             const MutableState &, const ImmutableState &)
  {
    LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant extra input recording channel %u", c);
    return 0;
  }

  static void Print(char *, const MutableState &, const ImmutableState &)
  {
  }
};
} // NeuronExtraInputModels
} // NeuronProcessor