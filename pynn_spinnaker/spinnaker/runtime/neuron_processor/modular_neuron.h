#pragma once

// Common includes
#include "../common/fixed_point_number.h"
#include "../common/log.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// NeuronProcessor::ModularNeuron
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
template<typename Dynamics, typename Input, typename Threshold>
class ModularNeuron
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const unsigned int RecordingChannelMax = Dynamics::RecordingChannelMax +\
                                                  Input::RecordingChannelMax +\
                                                  Threshold::RecordingChannelMax;

  //-----------------------------------------------------------------------------
  // MutableState
  //-----------------------------------------------------------------------------
  struct MutableState : Dynamics::MutableState, Input::MutableState,
                        Threshold::MutableState
  {
  };

  //-----------------------------------------------------------------------------
  // ImmutableState
  //-----------------------------------------------------------------------------
  struct ImmutableState : Dynamics::ImmutableState, Input::ImmutableState,
                          Threshold::ImmutableState
  {
  };

  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static inline bool Update(MutableState &mutableState, const ImmutableState &immutableState,
                            S1615 excInput, S1615 inhInput, S1615 extCurrent)
  {
    // Get membrane voltage from dynamics
    const S1615 membraneVoltage = Dynamics::GetMembraneVoltage(mutableState, immutableState);

    // Convert the excitatory and inhibitory inputs into a suitable input current
    const S1615 synapticInputCurrent = Input::GetInputCurrent(mutableState, immutableState,
                                                              excInput, inhInput, membraneVoltage);

    // Add together all sources of input current
    // **TODO** additional input
    const S1615 totalInputCurrent = synapticInputCurrent + extCurrent;

    // Update membrane dynamics to get new membrane voltage
    const S1615 newMembraneVoltage = Dynamics::Update(mutableState, immutableState,
                                                      totalInputCurrent);

    // Has this new membrane voltage crossed the threshold?
    const bool spike = Threshold::HasCrossed(mutableState, immutableState,
                                                    newMembraneVoltage);

    // If a spike occurs, notify dynamics
    // **TODO** notify additional input too
    if(spike)
    {
      Dynamics::SetSpiked(mutableState, immutableState);
    }

    return spike;

  }

  static S1615 GetRecordable(unsigned int c,
                             const MutableState &mutableState, const ImmutableState &immutableState,
                             S1615 excInput, S1615 inhInput)
  {
    // If recording channel comes from neuron dynamics
    if(c < Dynamics::RecordingChannelMax)
    {
      return Dynamics::GetRecordable((typename Dynamics::RecordingChannel)c,
                                     mutableState, immutableState);
    }


    // Otherwise, if recording channel comes from neuron input
    c -= Dynamics::RecordingChannelMax;
    if(c < Input::RecordingChannelMax)
    {
      return Input::GetRecordable((typename Input::RecordingChannel)c,
                                  mutableState, immutableState,
                                  excInput, inhInput);
    }

    // **TODO** additional input
    // Otherwise, if recording channel comes from spiking threshold
    c -= Input::RecordingChannelMax;
    if(c < Threshold::RecordingChannelMax)
    {
      return Threshold::GetRecordable((typename Threshold::RecordingChannel)c,
                                      mutableState, immutableState);
    }
    // Otherwise
    else
    {
      LOG_PRINT(LOG_LEVEL_WARN, "Attempting to get data from non-existant dynamics recording channel %u", c);
      return 0;
    }
  }

  static void Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState)
  {
    // Print from all modules of neuron
    Dynamics::Print(stream, mutableState, immutableState);
    Input::Print(stream, mutableState, immutableState);
    Threshold::Print(stream, mutableState, immutableState);
  }
};
} // NeuronProcessor