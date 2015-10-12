#pragma once

// Common includes
#include "../../common/fixed_point_number.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronModels
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronModels
{
//-----------------------------------------------------------------------------
// LIFCurr
//-----------------------------------------------------------------------------
class LIFCurr
{
public:
  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState
  {
    // Membrane voltage [mV]
    S1615 m_V_Membrane;

    // Countdown to end of next refractory period [machine timesteps]
    int32_t m_RefractoryTimer;
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState
  {
    // Membrane voltage threshold at which neuron spikes [mV]
    S1615 m_V_Threshold;

    // Post-spike reset membrane voltage [mV]
    S1615 m_V_Reset;

    // Membrane resting voltage [mV]
    S1615 m_V_Rest;

    // Offset current [nA] but take care because actually 'per timestep charge'
    S1615 m_I_Offset;

    // Membrane resistance [MegaOhm]
    S1615 m_R_Membrane;

    // 'Fixed' computation parameter - time constant multiplier for
    // Closed-form solution
    // exp( -(machine time step in ms)/(R * C) ) [.]
    S1615 m_ExpTC;

    // Refractory time of neuron [machine timesteps]
    int32_t m_T_Refractory;
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline bool Update(MutableState &mutableState, const ImmutableState &immutableState,
                            S1615 excInput, S1615 inhInput, S1615 extBiasCurrent)
  {
    bool spike = false;

    // Update refractory timer
    mutableState.m_RefractoryTimer--;

    // If outside of the refractory period
    if (mutableState.m_RefractoryTimer <= 0)
    {
      // Get the input in nA
      S1615 inputThisTimestep = excInput - inhInput
        + extBiasCurrent + immutableState.m_I_Offset;

      // Convert input from current to voltage
      S1615 alpha = MulS1615(inputThisTimestep, immutableState.m_R_Membrane) + immutableState.m_V_Rest;

      // Perform closed form update
      mutableState.m_V_Membrane = alpha - MulS1615(immutableState.m_ExpTC,
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