#pragma once

// Model includes
#include "../../input_buffer.h"
#include "../../intrinsic_plasticity_models/stub.h"
#include "../../modular_neuron.h"
#include "../../neuron_dynamics_models/if.h"
#include "../../neuron_input_models/cond.h"
#include "../../neuron_threshold_models/constant.h"
#include "../../neuron_extra_input_models/stub.h"
#include "../../synapse_models/exp.h"

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef ModularNeuron<NeuronDynamicsModels::IF, NeuronInputModels::Cond,
                      NeuronThresholdModels::Constant,
                      NeuronExtraInputModels::Stub> Neuron;
typedef SynapseModels::Exp Synapse;
typedef IntrinsicPlasticityModels::Stub IntrinsicPlasticity;

typedef InputBufferBase<uint32_t> InputBuffer;
};