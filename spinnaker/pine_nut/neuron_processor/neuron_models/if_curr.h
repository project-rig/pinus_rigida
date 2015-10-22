#pragma once

// Common includes
#include "../../common/fixed_point_number.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronModels::IFCurr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronModels
{
class IFCurr
{
public:
  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState
  {
    // Membrane voltage [mV]
    S1516 m_V_Membrane;

    // Countdown to end of next refractory period [machine timesteps]
    int32_t m_RefractoryTimer;
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Membrane voltage threshold at which neuron spikes [mV]
    S1516 m_V_Threshold;

    // Post-spike reset membrane voltage [mV]
    S1516 m_V_Reset;

    // Membrane resting voltage [mV]
    S1516 m_V_Rest;

    // Offset current [nA] but take care because actually 'per timestep charge'
    S1516 m_I_Offset;

    // Membrane resistance [MegaOhm]
    S1516 m_R_Membrane;

    // 'Fixed' computation parameter - time constant multiplier for
    // Closed-form solution
    // exp( -(machine time step in ms)/(R * C) ) [.]
    S1516 m_ExpTauM;

    // Refractory time of neuron [machine timesteps]
    int32_t m_T_Refractory;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline bool Update(MutableState &mutableState, const ImmutableState &immutableState,
                            S1516 excInput, S1516 inhInput, S1516 extBiasCurrent)
  {
    bool spike = false;

    // Update refractory timer
    mutableState.m_RefractoryTimer--;

    // If outside of the refractory period
    if (mutableState.m_RefractoryTimer <= 0)
    {
      // Get the input in nA
      S1516 inputThisTimestep = excInput - inhInput
        + extBiasCurrent + immutableState.m_I_Offset;

      // Convert input from current to voltage
      S1516 alpha = MulS1516_S1516(inputThisTimestep, immutableState.m_R_Membrane) + immutableState.m_V_Rest;

      // Perform closed form update
      mutableState.m_V_Membrane = alpha - MulS1516_S1516(immutableState.m_ExpTauM,
                                                         alpha - mutableState.m_V_Membrane);

      // Neuron spikes if membrane voltage has crossed threshold
      spike = (mutableState.m_V_Membrane >= immutableState.m_V_Threshold);
      if (spike)
      {
        // Reset membrane voltage
        mutableState.m_V_Membrane = immutableState.m_V_Reset;

        // Reset refractory timer
        mutableState.m_RefractoryTimer  = immutableState.m_T_Refractory;
      }
    }

    return spike;
  }

  static void Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState);
};
};  // namespace NeuronModels
};  // namespace NeuronProcessor