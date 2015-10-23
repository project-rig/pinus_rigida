#pragma once

// Model includes
#include "../../neuron_models/if_curr.h"
#include "../../synapse_models/exp.h"

namespace NeuronProcessor
{
//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef NeuronModels::IFCurr Neuron;
typedef SynapseModels::Exp Synapse;

};