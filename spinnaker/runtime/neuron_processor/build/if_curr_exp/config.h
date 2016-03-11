#pragma once

// Model includes
#include "../../input_buffer.h"
#include "../../neuron_models/if_curr.h"
#include "../../synapse_models/exp.h"

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef NeuronModels::IFCurr Neuron;
typedef SynapseModels::Exp Synapse;

typedef InputBufferBase<uint32_t> InputBuffer;
};