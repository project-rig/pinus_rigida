#pragma once

// Common includes
#include "../../common/fixed_point_number.h"
#include "../../common/log.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronInputModels
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronInputModels
{
//-----------------------------------------------------------------------------
// Curr
//-----------------------------------------------------------------------------
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
  static inline S1615 Update(MutableState &mutableState, const ImmutableState &immutableState,
                            S1615 excInput, S1615 inhInput, S1615 extCurrent)
  {
    // If outside of the refractory period
    if (mutableState.m_RefractoryTimer <= 0)
    {
      // Get the input in nA
      S1615 inputThisTimestep = excInput - inhInput
        + extCurrent + immutableState.m_I_Offset;

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tInput this timestep:%.4knA", inputThisTimestep);

      // Convert input from current to voltage
      S1615 alpha = MulS1615(inputThisTimestep, immutableState.m_R_Membrane) + immutableState.m_V_Rest;

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tAlpha:%.4kmV", alpha);

      // Perform closed form update
      mutableState.m_V_Membrane = alpha - MulS1615(immutableState.m_ExpTC,
                                                   alpha - mutableState.m_V_Membrane);

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tMembrane voltage:%.4knA", mutableState.m_V_Membrane);
    }
    // Otherwise, count down refractory timer
    else
    {
      mutableState.m_RefractoryTimer--;
    }

    // Return membrane voltage
    return mutableState.m_V_Membrane;
  }

  static void SetSpiked(MutableState &mutableState, const ImmutableState &immutableState)
  {
    // Reset membrane voltage
    mutableState.m_V_Membrane = immutableState.m_V_Reset;

    // Reset refractory timer
    mutableState.m_RefractoryTimer = immutableState.m_T_Refractory;
  }

  static S1615 GetRecordable(RecordingChannel c,
                             const MutableState &mutableState, const ImmutableState &,
                             S1615, S1615, S1615)
  {
    switch(c)
    {
      default:
        LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant recording channel %u", c);
        return 0;
    }
  }

  static void Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState);
};
};  // namespace NeuronInputModels
};  // namespace NeuronProcessor